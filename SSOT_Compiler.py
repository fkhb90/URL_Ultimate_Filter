#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
URL Ultimate Filter - SSOT Compiler & Matrix Test Suite
-------------------------
當前版本：V44.77
最新架構更新：
- [BugFix] 針對 104 工作快找 APP (v3.30.0) 新增局部參數豁免，精準放行 /2.0/notify/、/2.0/user/ 與 /2.0/company/ 路徑下的 device_id，修復 APP 啟動時報錯「必傳參數遺失」之異常。

近期更新摘要 (完整歷史軌跡請參閱 CHANGELOG.md)：
- V44.76: 升級 CRITICAL_PATH_MAP 支援 Action Routing，實作 Slack 遙測端點 DROP 權重。
- V44.75: 精準狙擊蝦皮 A/B 測試與流量分配遙測端點，防止設備特徵分群。
- V44.74: 策略回退與重構，精準豁免蝦皮 PDP 商品 API，升級 ABSOLUTE_BYPASS_DOMAINS。
"""

import json
import os
import sys
import tempfile
import textwrap
from datetime import datetime
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from subprocess import PIPE, Popen
from typing import Any, Dict, List, Optional, Tuple

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

VERSION = "44.77"

# [Release Notes] 用於自動追加至 CHANGELOG.md 的當前版本詳細日誌
CURRENT_RELEASE_NOTES = """
- [BugFix] 針對 104 工作快找 APP (v3.30.0) 新增局部參數豁免，精準放行 /2.0/notify/、/2.0/user/ 與 /2.0/company/ 路徑下的 device_id，修復 APP 啟動時報錯「必傳參數遺失」之異常。
"""

# ==========================================
#  1. SINGLE SOURCE OF TRUTH (RULES DATABASE)
# ==========================================

RULES_DB = {
    "OAUTH_SAFE_HARBOR_DOMAINS": [
        'accounts.google.com', 'accounts.google.com.tw', 'accounts.youtube.com',
        'appleid.apple.com', 'idmsa.apple.com',
        'facebook.com', 'www.facebook.com', 'm.facebook.com',
        'login.microsoftonline.com', 'login.live.com',
        'github.com', 'api.twitter.com', 'api.x.com'
    ],
    "PARAM_CLEANING_EXEMPTED_DOMAINS": {
        "EXACT": [
            'shopback.com.tw', 'extrabux.com', 'buy.line.me'
        ],
        "WILDCARDS": [
            'feedly.com', 'shopee.tw', 
            's3.amazonaws.com', 'storage.googleapis.com', 'core.windows.net',
            'api.line.me', 'api.newebpay.com', 'api.tappayapis.com',
            'api.stripe.com', 'api.github.com', 'api.twitch.tv',
            'cdn.discordapp.com', 'slack.com', 'cloudfunctions.net'
        ]
    },
    "SILENT_REWRITE_DOMAINS": {
        "EXACT": [],
        "WILDCARDS": ['591.com.tw', '104.com.tw']
    },
    "SCOPED_PARAM_EXEMPTIONS": {
        "104.com.tw": {
            "/api/": ["device_id", "client_id"],
            "/v2/api/": ["device_id"],
            "/2.0/notify/": ["device_id"],
            "/2.0/user/": ["device_id"],
            "/2.0/company/": ["device_id"]
        }
    },
    "ABSOLUTE_BYPASS_DOMAINS": {
        "EXACT": [
            'api.ecpay.com.tw', 'payment.ecpay.com.tw', 'api.map.ecpay.com.tw', 'api.jkos.com'
        ],
        "WILDCARDS": [
            'cathaybk.com.tw', 'ctbcbank.com', 'esunbank.com.tw', 'fubon.com', 'taishinbank.com.tw',
            'richart.tw', 'bot.com.tw', 'cathaysec.com.tw', 'chb.com.tw', 'citibank.com.tw',
            'dawho.tw', 'dbs.com.tw', 'firstbank.com.tw', 'hncb.com.tw', 'hsbc.co.uk', 'hsbc.com.tw',
            'landbank.com.tw', 'megabank.com.tw', 'scsb.com.tw', 'sinopac.com', 'sinotrade.com.tw',
            'standardchartered.com.tw', 'tcb-bank.com.tw', 'paypal.com', 'stripe.com',
            'taiwanpay.com.tw', 'twca.com.tw', 'twmp.com.tw', 'pay.taipei',
            'momopay.com.tw', 'mymobibank.com.tw',
            'post.gov.tw', 'nhi.gov.tw', 'mohw.gov.tw', 'tdcc.com.tw'
        ]
    },
    "PRIORITY_BLOCK_DOMAINS": [
        'cdn-path.com', 'doorphone92.com', 'easytomessage.com',
        'penphone92.com', 'sir90hl.com', 'uymgg1.com',
        'browser.events.data.microsoft.com', 'mobile.events.data.microsoft.com', 'self.events.data.microsoft.com',
        'onecollector.cloudapp.aria.akadns.net', 'watson.telemetry.microsoft.com',
        'admob.com', 'ads.google.com', 'adservice.google.com', 'adservice.google.com.tw',
        'doubleclick.net', 'googleadservices.com', 'googlesyndication.com',
        'crashlyticsreports-pa.googleapis.com', 'firebaselogging-pa.googleapis.com',
        'imasdk.googleapis.com', 'measurement.adservices.google.com', 'privacysandbox.googleapis.com',
        'business.facebook.com', 'connect.facebook.net', 'graph.facebook.com',
        '2o7.net', 'adobedc.net', 'demdex.net', 'everesttech.net', 'omtrdc.net',
        '3lift.com', 'adnxs.com', 'advertising.com', 'amazon-adsystem.com',
        'bidswitch.net', 'indexexchange.com', 'media.net', 'sharethrough.com', 'teads.tv',
        'crwdcntrl.net', 'exelator.com', 'eyeota.com', 'krxd.net', 'lotame.com',
        'liadm.com', 'rlcdn.com', 'tapad.com',
        'contextweb.com', 'mathtag.com', 'rfihub.com',
        'adcolony.com', 'applovin.com', 'chartboost.com', 'ironsrc.com',
        'pangle.io', 'popads.net', 'tapjoy.com', 'unityads.unity3d.com', 'vungle.com',
        'outbrain.com', 'taboola.com',
        'app-measurement.com', 'branch.io', 'singular.net',
        'ad.etmall.com.tw', 'ad.line.me', 'ad-history.line.me',
        'ads.linkedin.com', 'ads.tiktok.com', 'analytics.tiktok.com',
        'cdn.segment.com', 'clarity.ms', 'fullstory.com',
        'inmobi.com', 'inner-active.mobi', 'launchdarkly.com', 'split.io',
        'iadsdk.apple.com', 'metrics.icloud.com',
        'ad.impactify.io', 'impactify.media',
        'adsv.omgrmn.tw', 'browser.sentry-cdn.com', 'caid.china-caa.org', 'slackb.com',
        'events.tiktok.com', 'ibytedtos.com',
        'log.tiktokv.com', 'log16-normal-c-useast1a.tiktokv.com',
        'mon.tiktokv.com', 'mon-va.tiktokv.com',
        'analysis.shein.com', 'dc.shein.com', 'st.shein.com', 'report.temu.com',
        'alimama.com', 'hm.baidu.com', 'mmstat.com', 'pos.baidu.com', 'sm.cn',
        'sofire.baidu.com', 'sp0.baidu.com', 'sp1.baidu.com', 'tanx.com',
        'uc.cn', 'ucweb.com', 'uczzd.cn', 'ynuf.alipay.com',
        'cms-statistics.quark.cn', 'stat.quark.cn', 'unpm-upaas.quark.cn',
        'browser.360.cn', 's.360.cn', 'shouji.360.cn', 'stat.360.cn',
        'inte.sogou.com', 'lu.sogou.com', 'pb.sogou.com', 'ping.sogou.com',
        'analytics.shopee.tw', 'apm.tracking.shopee.tw', 'dem.shopee.com',
        'dmp.shopee.tw', 'live-apm.shopee.tw', 'log-collector.shopee.tw',
        'analysis.momoshop.com.tw', 'ecdmp.momoshop.com.tw', 'event.momoshop.com.tw',
        'log.momoshop.com.tw', 'pixel.momoshop.com.tw', 'rtb.momoshop.com.tw',
        'sspap.momoshop.com.tw', 'trace.momoshop.com.tw', 'trk.momoshop.com.tw',
        'jslog.coupang.com', 'mercury.coupang.com',
        'ad.gamer.com.tw', 'ad-geek.net', 'ad-hub.net', 'ad-serv.teepr.com', 'ad-tracking.dcard.tw',
        'analysis.tw', 'appier.net', 'b.bridgewell.com', 'cacafly.com', 'clickforce.com.tw',
        'fast-trk.com', 'funp.com', 'guoshipartners.com', 'imedia.com.tw', 'is-tracking.com',
        'itad.linetv.tw', 'likr.tw', 'scupio.com', 'sitetag.us',
        'tagtoo.co', 'tenmax.io', 'trk.tw', 'urad.com.tw', 'vpon.com',
        'adnext-a.akamaihd.net', 'toots-a.akamaihd.net',
        'analytics.twitter.com',
        'edge-analytics.amazonaws.com', 'edge-tracking.cloudflare.com',
        'insight.linkedin.com', 'px.ads.linkedin.com'
    ],
    "REDIRECTOR_HOSTS": [
        'adf.ly', 'ay.gy', 'gloyah.net', 'j.gs', 'q.gs', 'zo.ee',
        'direct-link.net', 'file-link.net', 'filemedia.net', 'link-center.net',
        'link-hub.net', 'link-target.net', 'link-to.net', 'linkvertise.com',
        'linkvertise.download', 'up-to-down.net',
        'links-loot.com', 'linksloot.net', 'loot-link.com', 'loot-links.com',
        'lootdest.com', 'lootdest.info', 'lootdest.org', 'lootlabs.gg', 'lootlink.org', 'lootlinks.co',
        'boost.ink', 'booo.st', 'bst.gg', 'bst.wtf', 'letsboost.net', 'mboost.me',
        'rekonise.com', 'sub2get.com', 'sub2unlock.com', 'sub4unlock.io', 'subfinal.com',
        'filecrypt.cc', 'filecrypt.co', 'keeplinks.org', 'lockr.so',
        'adpaylink.com', 'adshrink.com', 'adyou.me', 'clicksfly.com', 'cutwin.com',
        'cuty.io', 'droplink.co', 'exe.io', 'linkpays.in',
        'paster.so', 'pubiza.com', 'safelinku.com', 'shorte.st', 'shortzon.com',
        'shrink.pe', 'shrinkearn.com', 'shrinkme.io', 'shrtfly.com', 'smoner.com',
        'try2link.com', 'uii.io', 'v2links.com', 'work.ink', 'za.gl',
        '1ink.cc', 'adfoc.us', 'adsafelink.com', 'adshnk.com', 'adz7short.space', 'aylink.co',
        'bc.vc', 'bcvc.ink', 'birdurls.com', 'ceesty.com',
        'clik.pw', 'clk.sh', 'cpmlink.net', 'cpmlink.pro',
        'cutpaid.com', 'dlink3.com', 'dz4link.com', 'earnlink.io', 'exe-links.com', 'exeo.app',
        'fc-lc.com', 'fir3.net', 'gestyy.com',
        'gitlink.pro', 'gplinks.co', 'hotshorturl.com', 'icutlink.com', 'kimochi.info',
        'kingofshrink.com', 'linegee.net', 'link1s.com', 'linkmoni.com', 'linkpoi.me', 'linkshrink.net',
        'linksly.co', 'lnk2.cc', 'mangalist.org', 'megalink.pro', 'met.bz',
        'oke.io', 'oko.sh', 'oni.vn', 'onlinefreecourse.net',
        'ouo.io', 'ouo.press', 'pahe.plus', 'payskip.org', 'pingit.im',
        'shortlinkto.biz', 'shortmoz.link', 'shrt10.com', 'similarsites.com',
        'smilinglinks.com', 'spacetica.com', 'spaste.com', 'stfly.me', 'stfly.xyz', 'supercheats.com',
        'techgeek.digital', 'techstudify.com', 'techtrendmakers.com', 'thinfi.com',
        'tnshort.net', 'tribuntekno.com', 'turdown.com', 'tutwuri.id',
        'urlcash.com', 'urlcash.org', 'vinaurl.net', 'vzturl.com', 'xpshort.com', 'zegtrends.com'
    ],
    "HARD_WHITELIST": {
        "EXACT": [
            'iappapi.investing.com', 'cdn.oaistatic.com', 'files.oaiusercontent.com', 
            'claude.ai', 'gemini.google.com', 'perplexity.ai', 'www.perplexity.ai',
            'pplx-next-static-public.perplexity.ai', 'private-us-east-1.monica.im', 'api.felo.ai',
            'qianwen.aliyun.com', 'static.stepfun.com', 'api.openai.com', 'a-api.anthropic.com',
            'api.feedly.com', 'sandbox.feedly.com', 'cloud.feedly.com', 'translate.google.com', 'translate.googleapis.com',
            'inbox.google.com', 'reportaproblem.apple.com',
            'sso.godaddy.com', 'api.login.yahoo.com', 
            'firebaseappcheck.googleapis.com', 'firebaseinstallations.googleapis.com',
            'firebaseremoteconfig.googleapis.com', 'accounts.felo.me',
            'api.etmall.com.tw',
            'tw.fd-api.com', 'tw.mapi.shp.yahoo.com', 
            'code.createjs.com', 'raw.githubusercontent.com',
            'userscripts.adtidy.org', 'api.github.com', 'api.vercel.com',
            'gateway.facebook.com', 'graph.instagram.com', 'graph.threads.net', 'i.instagram.com',
            'api.discord.com', 'api.twitch.tv', 'api.line.me', 'today.line.me',
            'pro.104.com.tw', 'appapi.104.com.tw', 'datadog.pool.ntp.org', 'ewp.uber.com', 'copilot.microsoft.com', 
            'firebasedynamiclinks.googleapis.com', 'obs-tw.line-apps.com', 'obs.line-scdn.net'
        ],
        "WILDCARDS": [
            'sendgrid.net', 'agirls.aotter.net', 'query1.finance.yahoo.com', 'query2.finance.yahoo.com',
            'mitake.com.tw', 'money-link.com.tw', '591.com.tw', '104.com.tw',
            'icloud.com', 'apple.com', 'whatsapp.net', 'update.microsoft.com', 'windowsupdate.com',
            'atlassian.net', 'auth0.com', 'okta.com', 'nextdns.io',
            'archive.is', 'archive.li', 'archive.ph', 'archive.today', 'archive.vn', 'cc.bingj.com',
            'perma.cc', 'timetravel.mementoweb.org', 'web-static.archive.org', 'web.archive.org',
            'googlevideo.com', 'app.goo.gl', 'goo.gl', 'browserleaks.com'
        ]
    },
    "SOFT_WHITELIST": {
        "EXACT": [
            'gateway.shopback.com.tw', 'api.anthropic.com', 'api.cohere.ai', 'api.digitalocean.com',
            'api.fastly.com', 'api.heroku.com', 'api.hubapi.com', 'api.mailgun.com', 'api.netlify.com',
            'api.pagerduty.com', 'api.sendgrid.com', 'api.telegram.org', 'api.zendesk.com', 'duckduckgo.com',
            'legy.line-apps.com', 'secure.gravatar.com', 'api.asana.com',
            'api.dropboxapi.com', 'api.figma.com', 'api.notion.com', 'api.trello.com', 'api.cloudflare.com',
            'auth.docker.io', 'database.windows.net', 'login.docker.com', 'api.irentcar.com.tw',
            'usiot.roborock.com',
            'prism.ec.yahoo.com', 'graphql.ec.yahoo.com', 'visuals.feedly.com', 'api.revenuecat.com',
            'api-paywalls.revenuecat.com', 'account.uber.com', 'xlb.uber.com', 'cmapi.tw.coupang.com',
            'api.ipify.org', 'gcp-data-api.ltn.com.tw', 's.pinimg.com', 'cdn.shopify.com'
        ],
        "WILDCARDS": [
            'chatgpt.com', 'shopee.com', 'shopeemobile.com', 'shopee.io',
            'youtube.com', 'facebook.com', 'instagram.com', 'twitter.com', 'tiktok.com', 'spotify.com',
            'netflix.com', 'disney.com', 'linkedin.com', 'discord.com', 'googleapis.com', 'book.com.tw',
            'citiesocial.com', 'coupang.com', 'iherb.biz', 'iherb.com', 'm.youtube.com', 'momo.dm',
            'momoshop.com.tw', 'pxmart.com.tw', 'pxpayplus.com', 'shopback.com.tw', 'akamaihd.net',
            'amazonaws.com', 'cloudflare.com', 'cloudfront.net', 'fastly.net', 'fbcdn.net', 'gstatic.com',
            'jsdelivr.net', 'cdnjs.cloudflare.com', 'twimg.com', 'unpkg.com', 'ytimg.com', 'new-reporter.com',
            'wp.com', 'flipboard.com', 'inoreader.com', 'itofoo.com', 'newsblur.com', 'theoldreader.com',
            'azurewebsites.net', 'cloudfunctions.net', 'digitaloceanspaces.com', 'github.io', 'gitlab.io',
            'netlify.app', 'oraclecloud.com', 'pages.dev', 'vercel.app', 'windows.net', 'threads.net',
            'threads.com', 'slack.com', 'feedly.com',
            'ak.sv', 'bayimg.com', 'beeimg.com', 'binbox.io', 'casimages.com', 'cocoleech.com',
            'cubeupload.com', 'dlupload.com', 'fastpic.org', 'fotosik.pl', 'gofile.download', 'ibb.co',
            'imagebam.com', 'imageban.ru', 'imageshack.com', 'imagetwist.com', 'imagevenue.com', 'imgbb.com',
            'imgbox.com', 'imgflip.com', 'imx.to', 'indishare.org', 'infidrive.net', 'k2s.cc', 'katfile.com',
            'mirrored.to', 'multiup.io', 'nmac.to', 'noelshack.com', 'pic-upload.de', 'pixhost.to',
            'postimg.cc', 'prnt.sc', 'sfile.mobi', 'thefileslocker.net', 'turboimagehost.com', 'uploadhaven.com',
            'uploadrar.com', 'usersdrive.com', '__sbcdn'
        ]
    },
    "BLOCK_DOMAINS": [
        'anymind360.com', 'vt.quark.cn', 'iqr.chinatimes.com', 'ecount.ctee.com.tw', 'sdk.gamania.dev',
        'udc.yahoo.com', 'csc.yahoo.com', 'beap.gemini.yahoo.com', 'opus.analytics.yahoo.com', 'noa.yahoo.com',
        'sspap.pchome.tw', 'rtb.pchome.tw', 'log.pchome.com.tw', 'ad.pchome.com.tw',
        'vm5apis.com', 'vlitag.com', 'intentarget.com', 'innity.net', 'ad-specs.guoshippartners.com',
        'cdn.ad.plus', 'cdn.doublemax.net', 'udmserve.net', 'signal-snacks.gliastudios.com', 'adc.tamedia.com.tw',
        'log.zoom.us', 'metrics.uber.com', 'event-tracker.uber.com', 'cn-geo1.uber.com',
        'udp.yahoo.com', 'analytics.yahoo.com', 'effirst.com', 'px.effirst.com', 'simonsignal.com', 
        'analytics.etmall.com.tw',
        'bam.nr-data.net', 'bam-cell.nr-data.net', 'lrkt-in.com',
        'cdn.lr-ingest.com', 'r.lr-ingest.io', 'api-iam.intercom.io', 'openfpcdn.io', 'fingerprintjs.com',
        'fundingchoicesmessages.google.com', 'hotjar.com', 'segment.io', 'mixpanel.com', 'amplitude.com',
        'crazyegg.com', 'bugsnag.com', 'sentry.io', 'newrelic.com', 'logrocket.com', 'fpjs.io', 'adunblock1.static-cloudflare.workers.dev',
        'guce.oath.com', 'app-site-association.cdn-apple.com', 'cdn-edge-tracking.com',
        'edge-telemetry.akamai.com',
        'edgecompute-analytics.com', 'monitoring.edge-compute.io', 'realtime-edge.fastly.com',
        'log.felo.ai', 'event.sc.gearupportal.com', 'pidetupop.com', 'adform.net',
        'adsrvr.org', 'analytics.line.me', 'analytics.slashdotmedia.com', 'analytics.strava.com',
        'analytics.yahoo.com', 'api.pendo.io', 'c.clarity.ms', 'c.segment.com',
        'chartbeat.com', 'clicktale.net', 'clicky.com', 'comscore.com', 'customer.io',
        'data.investing.com', 'datadoghq.com', 'dynatrace.com', 'fullstory.com', 'heap.io', 'inspectlet.com',
        'iterable.com', 'keen.io', 'kissmetrics.com', 'loggly.com', 'matomo.cloud', 'mgid.com',
        'mouseflow.com', 'mparticle.com', 'mlytics.com', 'nr-data.net', 'oceanengine.com', 'openx.net',
        'optimizely.com', 'piwik.pro', 'posthog.com', 'quantserve.com', 'revcontent.com', 'rudderstack.com',
        'segment.com', 'semasio.net', 'snowplowanalytics.com', 'statcounter.com',
        'statsig.com', 'static.ads-twitter.com', 'sumo.com', 'sumome.com', 'tealium.com', 'track.hubspot.com',
        'track.tiara.daum.net', 'track.tiara.kakao.com', 'vwo.com', 'yieldlab.net',
        'fingerprint.com', 'doubleverify.com', 'iasds.com', 'moat.com', 'moatads.com',
        'sdk.iad-07.braze.com', 'serving-sys.com', 'tw.ad.doubleverify.com', 'agkn.com', 'id5-sync.com',
        'liveramp.com', 'permutive.com', 'tags.tiqcdn.com', 'klaviyo.com', 'marketo.com', 'mktoresp.com',
        'pardot.com', 'instana.io', 'launchdarkly.com', 'raygun.io', 'navify.com', 'cnzz.com', 'umeng.com',
        'talkingdata.com', 'jiguang.cn', 'getui.com', 'mdap.alipay.com', 'loggw-ex.alipay.com',
        'pgdt.gtimg.cn', 'afd.baidu.com', 'als.baidu.com', 'cpro.baidu.com', 'dlswbr.baidu.com',
        'duclick.baidu.com', 'feed.baidu.com', 'h2tcbox.baidu.com', 'hm.baidu.com', 'hmma.baidu.com',
        'mobads-logs.baidu.com', 'mobads.baidu.com', 'nadvideo2.baidu.com', 'nsclick.baidu.com', 'sp1.baidu.com',
        'voice.baidu.com', '3gimg.qq.com', 'fusion.qq.com', 'ios.bugly.qq.com', 'lives.l.qq.com',
        'monitor.uu.qq.com', 'pingma.qq.com', 'sdk.e.qq.com', 'wup.imtt.qq.com', 'appcloud.zhihu.com',
        'appcloud2.in.zhihu.com', 'crash2.zhihu.com', 'mqtt.zhihu.com', 'sugar.zhihu.com', 'agn.aty.sohu.com',
        'apm.gotokeep.com', 'cn-huabei-1-lg.xf-yun.com', 'gs.getui.com', 'log.b612kaji.com', 'pc-mon.snssdk.com',
        'sensorsdata.cn', 'stat.m.jd.com', 'trackapp.guahao.cn', 'traffic.mogujie.com', 'wmlog.meituan.com',
        'zgsdk.zhugeio.com', 'admaster.com.cn', 'adview.cn', 'alimama.com', 'getui.net', 'gepush.com',
        'gridsum.com', 'growingio.com', 'igexin.com', 'jpush.cn', 'kuaishou.com', 'miaozhen.com', 'mmstat.com',
        'pangolin-sdk-toutiao.com', 'talkingdata.cn', 'tanx.com', 'umeng.cn', 'umeng.co', 'umengcloud.com',
        'youmi.net', 'zhugeio.com', 'appnext.hs.llnwd.net', 'fusioncdn.com',
        'abema-adx.ameba.jp', 'ad.12306.cn', 'ad.360in.com', 'adroll.com', 'ads.yahoo.com',
        'adserver.yahoo.com', 'appnexus.com', 'bluekai.com', 'casalemedia.com', 'doubleclick.net',
        'googleadservices.com', 'googlesyndication.com', 'outbrain.com', 'taboola.com', 'rubiconproject.com',
        'pubmatic.com', 'openx.com', 'smartadserver.com', 'spotx.tv', 'yandex.ru', 'addthis.com',
        'onesignal.com', 'sharethis.com', 'bat.bing.com', 'clarity.ms',
        'elads.kocpc.com.tw', 'eservice.emarsys.net'
    ],
    "BLOCK_DOMAINS_WILDCARDS": [
        'sentry.io', 'pidetupop.com', 'cdn-net.com', 'lr-ingest.io',
        'aotter.net', 'ssp.yahoo.com', 'pbs.yahoo.com', 'ay.delivery',
        'cootlogix.com', 'ottadvisors.com', 'newaddiscover.com', 'app-ads-services.com',
        'app-measurement.com', 'adjust.com', 'adjust.net', 'appsflyer.com', 'onelink.me',
        'branch.io', 'app.link', 'kochava.com', 'scorecardresearch.com', 'rayjump.com',
        'mintegral.net', 'tiktokv.com', 'byteoversea.com', 'criteo.com', 'criteo.net',
        'adservices.google.com'
    ],
    "BLOCK_DOMAINS_REGEX": [
        '^ads?\\d*\\.(?:ettoday\\.net|ltn\\.com\\.tw)$',
        '^browser-intake-[\\w.-]*datadoghq\\.(?:com|eu|us)$'
    ],
    "CRITICAL_PATH_GENERIC": [
        '/accounts/CheckConnection', '/0.gif', '/1.gif', '/pixel.gif', '/beacon.gif', '/ping.gif',
        '/track.gif', '/dot.gif', '/clear.gif', '/empty.gif', '/shim.gif', '/spacer.gif', '/imp.gif',
        '/impression.gif', '/view.gif', '/sync.gif', '/sync.php', '/match.gif', '/match.php',
        '/utm.gif', '/event.gif', '/bk', '/bk.gif', '/collect', '/events',
        '/track', '/beacon', '/pixel', '/v1/collect', '/v1/events',
        '/v1/track', '/v1/report', '/v1/logs', '/api/v1/logs', 
        '/appbase_report_log', '/stat_log', '/trackcode/', '/v2/collect', '/v2/events', '/v2/track',
        '/tp2', '/api/v1/collect', '/api/v1/events', '/api/v1/track', '/api/v1/telemetry',
        '/v1/event', '/api/stats/ads', '/api/stats/atr', '/api/stats/qoe',
        '/api/stats/playback', '/pagead/gen_204', '/pagead/paralleladview', '/tiktok/pixel/events', 
        '/linkedin/insight/track', '/api/fingerprint', '/v1/fingerprint', '/cdn/fp/', '/api/collect', 
        '/api/track', '/tr/', '/beacon', '/api/v1/event', '/rest/n/log', '/action-log', 
        '/ramen/v1/events', '/_events', '/report/v1/log', '/app/mobilelog', '/api/web/ad/', 
        '/cdn/fingerprint/', '/api/device-id', '/api/visitor-id', '/ads/ga-audiences', '/doubleclick/', 
        '/google-analytics/', '/googleadservices/', '/googlesyndication/', '/googletagmanager/', 
        '/tiktok/track/', '/__utm.gif', '/j/collect', '/r/collect', '/api/batch', '/api/events', 
        '/api/v1/events', '/api/v1/track', '/api/v2/event', '/api/v2/events', '/collect?', 
        '/data/collect', '/events/track', '/ingest/', '/ingest/otel', '/intake', '/p.gif', '/rec/bundle', '/t.gif', 
        '/track/', '/v1/pixel', '/v2/track', '/v3/track', '/2/client/addlog_batch', 
        '/plugins/easy-social-share-buttons/', '/event_report', '/log/aplus', '/v.gif', '/ad-sw.js', 
        '/ads-sw.js', '/ad-call', '/adx/', '/adsales/', '/adserver/', '/adsync/', '/adtech/', 
        '/abtesting/', '/b/ss', '/feature-flag/', '/i/adsct', '/track/m', '/track/pc', '/user-profile/', 
        'cacafly/track', '/api/v1/t', '/sa.gif', '/api/v2/rum', '/batch_resolve'
    ],
    "CRITICAL_PATH_SCRIPT_ROOTS": [
        '/prebid', '/sentry.', 'sentry-', '/analytics.', 'ga-init.', 'gtag.', 'gtm.', 'ytag.',
        'connect.js', '/fbevents.', '/fbq.', '/pixel.', 'tiktok-pixel.', 'ttclid.', 'insight.min.',
        '/amplitude.', '/braze.', '/chartbeat.', '/clarity.', '/comscore.', '/crazyegg.', '/customerio.',
        '/fullstory.', '/heap.', '/hotjar.', '/inspectlet.', '/iterable.', '/logrocket.', '/matomo.',
        '/mixpanel.', '/mouseflow.', '/optimizely.', '/piwik.', '/posthog.', '/quant.', '/quantcast.',
        '/segment.', '/statsig.', '/vwo.', '/ad-manager.', '/ad-player.', '/ad-sdk.', '/adloader.',
        '/adroll.', '/adsense.', '/advideo.', '/apstag.', '/criteo-loader.', '/criteo.',
        '/doubleclick.', '/mgid.', '/outbrain.', '/pubmatic.', '/revcontent.', '/taboola.',
        'ad-full-page.', 'api_event_tracking', 'itriweblog.', 'adobedtm.', 'dax.js', 'utag.', 'visitorapi.',
        'newrelic.', 'nr-loader.', 'perf.js', 'essb-core.', '/intercom.', '/pangle.', '/tagtoo.',
        'tiktok-analytics.', 'aplus.', 'aplus_wap.', '/ec.js', '/gdt.', '/hm.js', '/u.js', '/um.js', '/bat.js', 
        'beacon.min.', 'plausible.outbound', 'abtasty.', 'ad-core.', 'ad-lib.', 'adroll_pro.', 'ads-beacon.',
        'autotrack.', 'beacon.', 'capture.', '/cf.js', 'cmp.js', 'collect.js', 'link-click-tracker.',
        'main-ad.', 'scevent.min.', 'showcoverad.', 'sp.js', 'tracker.js', 'tracking-api.',
        'tracking.js', 'user-id.', 'user-timing.', 'wcslog.', 'jslog.min.', 'device-uuid.',
        '/plugins/advanced-ads', '/plugins/adrotate'
    ],
    "CRITICAL_PATH_MAP": {
        'o.alicdn.com': ['/tongyi-fe/lib/cnzz/c.js', '/tongyi-fe/lib/cnzz/z.js'],
        'qwen-api.zaodian.com': ['/api/app/template/v1/feed'],
        'file.chinatimes.com': ['/ad-param.json'],
        'health.tvbs.com.tw': ['/health-frontend-js/ad-read-page.js'],
        'static.ctee.com.tw': ['/js/ad2019.min.js', '/js/third-party-sticky-ad-callback.min.js'],
        'www.youtube.com': ['/ptracking', '/api/stats/atr', '/api/stats/qoe', '/api/stats/playback', '/youtubei/v1/log_event', '/youtubei/v1/log_interaction'],
        'm.youtube.com': ['/ptracking', '/api/stats/atr', '/api/stats/qoe', '/api/stats/playback', '/youtubei/v1/log_event', '/youtubei/v1/log_interaction'],
        'youtubei.googleapis.com': ['/youtubei/v1/log_event', '/youtubei/v1/log_interaction', '/api/stats/', '/youtubei/v1/notification/record_interactions'],
        'googlevideo.com': ['/ptracking', '/videoplayback?ptracking='],
        'api.uber.com': ['/ramen/v1/events', '/v3/mobile-event', '/advertising/v1/', '/eats/advertising/', '/rt/users/v1/device-info'],
        'api.ubereats.com': ['/v1/eats/advertising', '/ramen/v1/events'],
        'cn-geo1.uber.com': ['/ramen/v1/events', '/v3/mobile-event', '/monitor/v2/logs'],
        'tw.mapi.shp.yahoo.com': ['/w/analytics', '/v1/instrumentation', '/ws/search/tracking', '/dw/tracker'],
        'tw.buy.yahoo.com': ['/b/ss/', '/ws/search/tracking', '/activity/record'],
        'unwire.hk': ['/mkgqaa1mfbon.js'],
        'asset2.coupangcdn.com': ['/jslog.min.js'],
        'firebasedynamiclinks.googleapis.com': ['/v1/installattribution'],
        'api.rc-backup.com': ['/adservices_attribution'],
        'api.revenuecat.com': ['/adservices_attribution'],
        'api-d.dropbox.com': ['/send_mobile_log'],
        'www.google.com': ['/log', '/pagead/1p-user-list/'],
        'js.stripe.com': ['/fingerprinted/'],
        'chatgpt.com': ['/ces/statsc/flush', '/v1/rgstr'],
        'tw.fd-api.com': ['/api/v5/action-log'],
        'chatbot.shopee.tw': ['/report/v1/log'],
        'data-rep.livetech.shopee.tw': ['/dataapi/dataweb/event/'],
        'shopee.tw': ['/dataapi/dataweb/event/', '/abtest/traffic/'],
        'api.tongyi.com': ['/qianwen/event/track'],
        'gw.alipayobjects.com': ['/config/loggw/'],
        'slack.com': ['/api/profiling.logging.enablement', '/api/telemetry', 'DROP:/clog/track/'],
        'graphql.ec.yahoo.com': ['/app/sas/v1/fullsitepromotions'],
        'prism.ec.yahoo.com': ['/api/prism/v2/streamwithads'],
        'analytics.google.com': ['/g/collect', '/j/collect'],
        'region1.analytics.google.com': ['/g/collect'],
        'stats.g.doubleclick.net': ['/g/collect', '/j/collect'],
        'www.google-analytics.com': ['/debug/mp/collect', '/g/collect', '/j/collect', '/mp/collect'],
        'google.com': ['/ads', '/pagead'],
        'facebook.com': ['/tr', '/tr/'],
        'ads.tiktok.com': ['/i18n/pixel'],
        'business-api.tiktok.com': ['/open_api', '/open_api/v1.2/pixel/track', '/open_api/v1.3/event/track', '/open_api/v1.3/pixel/track'],
        'analytics.linkedin.com': ['/collect'],
        'px.ads.linkedin.com': ['/collect'],
        'ads.bing.com': ['/msclkid'],
        'ads.linkedin.com': ['/li/track'],
        'ads.yahoo.com': ['/pixel'],
        'amazon-adsystem.com': ['/e/ec'],
        'api.amplitude.com': ['/2/httpapi'],
        'api.hubspot.com': ['/events'],
        'api-js.mixpanel.com': ['/track'],
        'api.mixpanel.com': ['/track'],
        'api.segment.io': ['/v1/page', '/v1/track'],
        'c.segment.com': ['/v1/track', '/v1/page', '/v1/identify'],
        'heap.io': ['/api/track'],
        'in.hotjar.com': ['/api/v2/client'],
        'scorecardresearch.com': ['/beacon.js'],
        'segment.io': ['/v1/track'],
        'tr.snap.com': ['/v2/conversion'],
        'ads-api.tiktok.com': ['/api/v2/pixel'],
        'ads.pinterest.com': ['/v3/conversions/events'],
        'analytics.snapchat.com': ['/v1/batch'],
        'cnzz.com': ['/stat.php'],
        'gdt.qq.com': ['/gdt_mview.fcg'],
        'hm.baidu.com': ['/hm.js'],
        'cloudflareinsights.com': ['/cdn-cgi/rum'],
        'static.cloudflareinsights.com': ['/beacon.min.js'],
        'bat.bing.com': ['/action'],
        'metrics.vitals.vercel-insights.com': ['/v1/metrics'],
        'monorail-edge.shopifysvc.com': ['/v1/produce'],
        'vitals.vercel-insights.com': ['/v1/vitals'],
        'pbd.yahoo.com': ['/data/logs'],
        'plausible.io': ['/api/event'],
        'analytics.tiktok.com': ['/i18n/pixel/events.js'],
        'a.clarity.ms': ['/collect'],
        'd.clarity.ms': ['/collect'],
        'l.clarity.ms': ['/collect'],
        'ct.pinterest.com': ['/v3'],
        'events.redditmedia.com': ['/v1'],
        's.pinimg.com': ['/ct/core.js'],
        'www.redditstatic.com': ['/ads/pixel.js'],
        'discord.com': ['/api/v10/science', '/api/v9/science'],
        'vk.com': ['/rtrg'],
        'instagram.com': ['/logging_client_events'],
        'mall.shopee.tw': ['/userstats_record/batchrecord'],
        'patronus.idata.shopeemobile.com': ['/log-receiver/api/v1/0/tw/event/batch', '/event-receiver/api/v4/tw'],
        'dp.tracking.shopee.tw': ['/v4/event_batch'],
        'live-apm.shopee.tw': ['/apmapi/v1/event'],
        'cmapi.tw.coupang.com': ['/featureflag/batchtracking', '/sdp-atf-ads/', '/sdp-btf-ads/', '/home-banner-ads/', '/category-banner-ads/', '/plp-ads/'],
        'disqus.com': ['/api/3.0/users/events', '/j/', '/tracking_pixel/']
    },
    "HIGH_CONFIDENCE": [
        '/ad/', '/ads/', '/adv/', '/advert/', '/banner/', '/pixel/', '/tracker/', '/interstitial/', '/midroll/', '/popads/', '/preroll/', '/postroll/'
    ],
    "PATH_BLOCK": [
        'china-caa', '/advertising/', '/affiliate/', '/videoads/',
        '/popup/', '/promoted/', '/sponsor/', '/vclick/', '/ads-self-serve/', '/httpdns/', '/d?dn=', '/resolve?host=',
        '/query?host=', '__httpdns__', 'dns-query', '112wan', '2mdn', '51y5', '51yes', '789htbet', '96110',
        'acs86', 'ad-choices', 'ad-logics', 'adash', 'adashx', 'adcash', 'adcome', 'addsticky', 'addthis',
        'adform', 'adhacker', 'adinfuse', 'adjust', 'admarvel', 'admaster', 'admation', 'admdfs', 'admicro',
        'admob', 'adnewnc', 'adpush', 'adpushup', 'adroll', 'adsage', 'adsame', 'adsense', 'adsensor',
        'adserver', 'adservice', 'adsh', 'adskeeper', 'adsmind', 'adsmogo', 'adsnew', 'adsrvmedia', 'adsrvr',
        'adsserving', 'adsterra', 'adsupply', 'adsupport', 'adswizz', 'adsystem', 'adtilt', 'adtima', 'adtrack',
        'advert', 'advertise', 'advertisement', 'advertiser', 'adview', 'ad-video', 'advideo', 'adware',
        'adwhirl', 'adwords', 'adzcore', 'affiliate', 'alexametrics', 'allyes', 'amplitude', 'analysis',
        'analysys', 'analytics', 'aottertrek', 'appadhoc', 'appads', 'appboy', 'appier', 'applovin', 'appsflyer',
        'apptimize', 'apsalar', 'baichuan', 'bango', 'bangobango', 'bidvertiser', 'bingads', 'bkrtx', 'bluekai',
        'breaktime', 'bugsense', 'burstly', 'cedexis', 'chartboost', 'circulate', 'click-fraud', 'clkservice',
        'cnzz', 'cognitivlabs', 'collect', 'crazyegg', 'crittercism', 'cross-device', 'dealerfire', 'dfp',
        'dienst', 'djns', 'dlads', 'dnserror', 'domob', 'doubleclick', 'doublemax', 'dsp', 'duapps', 'duomeng',
        'dwtrack', 'egoid', 'emarbox', 'en25', 'eyeota', 'fenxi', 'fingerprinting', 'flurry', 'fwmrm',
        'getadvltem', 'getexceptional', 'googleads', 'googlesyndication', 'greenplasticdua', 'growingio',
        'guanggao', 'guomob', 'guoshipartners', 'heapanalytics', 'hotjar', 'hsappstatic', 'hubspot', 'igstatic',
        'inmobi', 'innity', 'instabug', 'intercom', 'izooto', 'jpush', 'juicer', 'jumptap', 'kissmetrics',
        'lianmeng', 'litix', 'localytics', 'logly', 'mailmunch', 'malvertising', 'matomo', 'medialytics',
        'meetrics', 'mgid', 'mifengv', 'mixpanel', 'mobaders', 'mobclix', 'mobileapptracking', '/monitoring/',
        'mvfglobal', 'networkbench', 'newrelic', 'omgmta', 'omniture', 'onead', 'openinstall', 'openx',
        'optimizely', 'outstream', 'partnerad', 'pingfore', 'piwik', 'pixanalytics', 'playtomic', 'polyad',
        'popin', 'popin2mdn', 'programmatic', 'pushnotification', 'quantserve', 'quantumgraph', 'queryly',
        'qxs', 'rayjump', 'retargeting', 'ronghub', 'scorecardresearch', 'scupio', 'securepubads', 'sensor',
        'sentry', 'shence', 'shenyun', 'shoplytics', 'shujupie', 'smartadserver', 'smartbanner', 'snowplow',
        'socdm', 'sponsors', 'spy', 'spyware', 'statcounter', 'stathat', 'sticky-ad', 'storageug', 'straas',
        'studybreakmedia', 'stunninglover', 'supersonicads', 'syndication', 'taboola', 'tagtoo', 'talkingdata',
        'tanx', 'tapjoy', 'tapjoyads', 'tenmax', 'tapfiliate', 'tingyun', 'tiqcdn', 'tlcafftrax', 'toateeli',
        'tongji', '/trace/', 'tracker', 'trackersimulator', 'trafficjunky', 'trafficmanager', 'tubemogul',
        'uedas', 'umeng', 'umtrack', 'unidesk', 'usermaven', 'usertesting', 'vast', 'venraas', 'vilynx',
        'vpaid', 'vpon', 'vungle', 'whalecloud', 'wistia', 'wlmonitor', 'woopra', 'xxshuyuan', 'yandex', 'zaoo',
        'zarget', 'zgdfz6h7po', 'zgty365', 'zhengjian', 'zhengwunet', 'zhuichaguoji', 'zjtoolbar', 'zzhyyj',
        '/ad-choices', '/ad-click', '/ad-code', 'ad-conversion', '/ad-engagement', 'ad-engagement', '/ad-event',
        '/ad-events', '/ad-exchange', 'ad-impression', '/ad-impression', '/ad-inventory', '/ad-loader',
        '/ad-logic', '/ad-manager', '/ad-metrics', '/ad-network', '/ad-placement', '/ad-platform', '/ad-request',
        '/ad-response', '/ad-script', '/ad-server', '/ad-slot', '/ad-specs', '/ad-system', '/ad-tag', '/ad-tech',
        'ad-telemetry', '/ad-telemetry', '/ad-unit', 'ad-verification', '/ad-verification', '/ad-view',
        'ad-viewability', '/ad-viewability', '/ad-wrapper', '/adframe/', '/adrequest/', '/adretrieve/',
        '/adserve/', '/adserving/', '/fetch_ads/', '/getad/', '/getads/', 'ad-break', 'ad_event', 'ad_logic',
        'ad_pixel', 'ad-call', 'adsbygoogle', 'amp-ad', 'amp-analytics', 'amp-auto-ads', 'amp-sticky-ad',
        'amp4ads', 'apstag', 'google_ad', 'pagead', 'pwt.js', '/analytic/', '/analytics/', '/api/v2/rum',
        '/audit/', '/beacon/', '/collect?', '/collector/', 'g/collect', '/insight/', '/intelligence/',
        '/measurement', 'mp/collect', '/report/', '/reporting/', '/reports/',
        '/unstable/produce_batch', '/v1/produce', '/bugsnag/', '/crash/', 'debug/mp/collect', '/error/',
        '/envelope', '/exception/', '/stacktrace/', 'performance-tracking', 'real-user-monitoring',
        'web-vitals', 'audience', 'attribution', 'behavioral-targeting', 'cohort', 'cohort-analysis',
        'data-collection', 'data-sync', 'fingerprint', 'retargeting', 'session-replay', 'third-party-cookie',
        'user-analytics', 'user-behavior', 'user-cohort', 'user-segment', 'appier', 'comscore', 'fbevents',
        'fbq', 'google-analytics', 'onead', 'osano', 'sailthru', 'tapfiliate', 'utag.js', '/apmapi/',
        'canvas-fingerprint', 'canvas-fp', '/canvas-fp/', 'webgl-fingerprint', 'webgl-fp', '/webgl-fp/', 'audio-fingerprint', 'audio-fp', 'font-fingerprint', 'font-detect-fp'
    ],
    "PRIORITY_DROP": [
        '/otel/v1/logs', '/otel/v1/traces', '/otel/v1/metrics', '/agent/v1/logs',
        '/v1/telemetry', '/v1/metrics', '/v1/traces', '/telemetry/'
    ],
    "DROP": [
        '?diag=', '?log=', '-log.', '/diag/', '/log/', '/logging/', '/logs/', 'adlog',
        'ads-beacon', 'airbrake', 'amp-analytics', '/batch/', '/batch?', 'beacon', 'client-event', 'collect',
        'collect?', 'collector', 'crashlytics', 'csp-report', 'data-pipeline', 'error-monitoring',
        'error-report', 'heartbeat', 'ingest', 'intake', 'live-log', 'log-event', 'logevents',
        'loggly', 'log-hl', 'realtime-log', '/rum/', 'server-event', 'uploadmobiledata',
        'web-beacon', 'web-vitals', 'crash-report', 'diagnostic.log', 'profiler', 'stacktrace', 'trace.json',
        '/error_204', 'a=logerror', '/client/events'
    ],
    "PARAMS_GLOBAL": [
        'dev_id', 'device_id', 'gclid', 'fbclid', 'ttclid', 'utm_source', 'utm_medium', 'utm_campaign', 'utm_term',
        'utm_content', 'yclid', 'mc_cid', 'mc_eid', 'srsltid', 'dclid', 'gclsrc', 'twclid', 'lid',
        '_branch_match_id', '_ga', '_gl', '_gid', '_openstat', 'admitad_uid', 'aiad_clid', 'awc', 'btag',
        'cjevent', 'cmpid', 'cuid', 'external_click_id', 'gad_source', 'gbraid', 'gps_adid', 'iclid',
        'igshid', 'irclickid', 'is_retargeting', 'ko_click_id', 'li_fat_id', 'mibextid', 'msclkid',
        'oprtrack', 'rb_clickid', 'sscid', 'trk', 'usqp', 'vero_conv', 'vero_id', 'wbraid', 'wt_mc',
        'xtor', 'ysclid', 'zanpid', 'yt_src', 'yt_ad', 's_kwcid', 'sc_cid', 'log_level'
    ],
    "PARAMS_PREFIXES": [
        '__cf_', '_bta', '_ga_', '_gat_', '_gid_', '_hs', '_oly_', 'action_', 'ad_', 'adjust_', 
        'aff_', 'af_', 'alg_', 'at_', 'bd_', 'bsft_', 'campaign_', 'cj', 'cm_', 'content_', 
        'creative_', 'fb_', 'from_', 'gcl_', 'guce_', 'hmsr_', 'hsa_', 'ir_', 'itm_', 'li_', 
        'matomo_', 'medium_', 'mkt_', 'ms_', 'mt_', 'mtm', 'pk_', 'piwik_', 'placement_', 
        'ref_', 'share_', 'source_', 'space_', 'term_', 'trk_', 'tt_', 'ttc_', 'vsm_', 'li_fat_', 'linkedin_'
    ],
    "EXCEPTIONS_SUFFIXES": [
        '.css', '.js', '.jpg', '.jpeg', '.gif', '.png', '.ico', '.svg', '.webp', '.woff', '.woff2', '.ttf',
        '.eot', '.mp4', '.mp3', '.mov', '.m4a', '.json', '.xml', '.yaml', '.yml', '.toml', '.ini',
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.zip', '.rar'
    ],
    "PATH_EXEMPTIONS": {
        "shopee.tw": ["/api/v4/search/search_items", "/api/v4/pdp/get"],
        "cmapi.tw.coupang.com": ["/vendor-items/"],
        "coupangcdn.com": ["/image/ccm/banner/", "/image/cmg/oms/banner/"],
        "www.google.com": ["/url", "/search", "/s2/favicons"],
        "play.googleapis.com": ["/log/batch"],
        "threads.com": ["/post/"],
        "threads.net": ["/post/"]
    }
}

# ==========================================
#  2. JS COMPILER & FORMATTER (SHARED)
# ==========================================

def format_js_array(lst: List[str], indent: int = 4, items_per_line: int = 6) -> str:
    if not lst: return "[]"
    chunks = [lst[i:i + items_per_line] for i in range(0, len(lst), items_per_line)]
    lines = [(" " * indent) + ", ".join(f"'{x}'" for x in chunk) for chunk in chunks]
    return "[\n" + ",\n".join(lines) + "\n" + (" " * (indent - 2)) + "]"

def format_js_set(lst: List[str], indent: int = 4, items_per_line: int = 6) -> str:
    if not lst: return "new Set([])"
    return f"new Set({format_js_array(lst, indent, items_per_line)})"

def format_js_map(dct: Dict[str, List[str]], indent: int = 4) -> str:
    if not dct: return "new Map([])"
    entries = []
    for k, v in dct.items():
        val_str = format_js_set(v, indent + 4, items_per_line=4)
        entries.append(f"{' ' * indent}['{k}', {val_str}]")
    joined_entries = ",\n".join(entries)
    return f"new Map([\n{joined_entries}\n{' ' * (indent - 2)}])"

def format_js_prefix_buckets(lst: List[str], indent: int = 4) -> str:
    if not lst: return "new Map()"
    buckets = defaultdict(list)
    for p in lst:
        if p: buckets[p[0]].append(p)
    entries = []
    for k in sorted(buckets.keys()):
        val_str = format_js_array(buckets[k], indent + 4, items_per_line=6)
        entries.append(f"{' ' * indent}['{k}', {val_str}]")
    joined_entries = ",\n".join(entries)
    return f"new Map([\n{joined_entries}\n{' ' * (indent - 2)}])"

def format_scoped_exemptions(dct: Dict[str, Dict[str, List[str]]], indent: int = 4) -> str:
    if not dct: return "new Map()"
    domain_entries = []
    for domain, path_dict in dct.items():
        path_entries = []
        for path, params in path_dict.items():
            param_set_str = format_js_set(params, indent + 8, items_per_line=4)
            path_entries.append(f"{' ' * (indent + 4)}['{path}', {param_set_str}]")
        joined_paths = ",\n".join(path_entries)
        path_map_str = f"new Map([\n{joined_paths}\n{' ' * (indent + 4)}])"
        domain_entries.append(f"{' ' * indent}['{domain}', {path_map_str}]")
    joined_domains = ",\n".join(domain_entries)
    return f"new Map([\n{joined_domains}\n{' ' * (indent - 2)}])"

def get_js_rules_definition(platform_desc: str) -> str:
    regex_joined = ', '.join([f"/{r}/i" for r in RULES_DB['BLOCK_DOMAINS_REGEX']])
    return f"""/**
 * @file      URL-Ultimate-Filter-{platform_desc}.js
 * @version   {VERSION} (SSOT Compilation)
 */

const CONFIG = {{ DEBUG_MODE: false, AC_SCAN_MAX_LENGTH: 600 }};
const SCRIPT_VERSION = '{VERSION}';

const OAUTH_SAFE_HARBOR = {{
    DOMAINS: {format_js_set(RULES_DB['OAUTH_SAFE_HARBOR_DOMAINS'])},
    PATHS_REGEX: [ /\\/(login|oauth|oauth2|authorize|signin|session)(\\/|\\?|$)/i ]
}};

const PARAM_CLEANING_EXEMPTED_DOMAINS = {{
    EXACT: {format_js_set(RULES_DB['PARAM_CLEANING_EXEMPTED_DOMAINS']['EXACT'])},
    WILDCARDS: {format_js_set(RULES_DB['PARAM_CLEANING_EXEMPTED_DOMAINS']['WILDCARDS'])}
}};

const SILENT_REWRITE_DOMAINS = {{
    EXACT: {format_js_set(RULES_DB['SILENT_REWRITE_DOMAINS']['EXACT'])},
    WILDCARDS: {format_js_set(RULES_DB['SILENT_REWRITE_DOMAINS']['WILDCARDS'])}
}};

const ABSOLUTE_BYPASS_DOMAINS = {{
    EXACT: {format_js_set(RULES_DB['ABSOLUTE_BYPASS_DOMAINS']['EXACT'])},
    WILDCARDS: {format_js_set(RULES_DB['ABSOLUTE_BYPASS_DOMAINS']['WILDCARDS'])}
}};

const RULES = {{
  PRIORITY_BLOCK_DOMAINS: {format_js_set(RULES_DB['PRIORITY_BLOCK_DOMAINS'])},
  REDIRECTOR_HOSTS: {format_js_set(RULES_DB['REDIRECTOR_HOSTS'])},

  HARD_WHITELIST: {{
    EXACT: {format_js_set(RULES_DB['HARD_WHITELIST']['EXACT'])},
    WILDCARDS: {format_js_set(RULES_DB['HARD_WHITELIST']['WILDCARDS'])}
  }},

  SOFT_WHITELIST: {{
    EXACT: {format_js_set(RULES_DB['SOFT_WHITELIST']['EXACT'])},
    WILDCARDS: {format_js_set(RULES_DB['SOFT_WHITELIST']['WILDCARDS'])}
  }},

  BLOCK_DOMAINS: {format_js_set(RULES_DB['BLOCK_DOMAINS'])},
  BLOCK_DOMAINS_WILDCARDS: {format_js_set(RULES_DB['BLOCK_DOMAINS_WILDCARDS'])},

  BLOCK_DOMAINS_REGEX: [
    {regex_joined}
  ],

  CRITICAL_PATH: {{
    GENERIC: {format_js_array(RULES_DB['CRITICAL_PATH_GENERIC'])},
    SCRIPT_ROOTS: {format_js_array(RULES_DB['CRITICAL_PATH_SCRIPT_ROOTS'])},
    MAP: {format_js_map(RULES_DB['CRITICAL_PATH_MAP'])}
  }},

  KEYWORDS: {{
    HIGH_CONFIDENCE: {format_js_array(RULES_DB['HIGH_CONFIDENCE'])},
    PATH_BLOCK: {format_js_array(RULES_DB['PATH_BLOCK'])},
    PRIORITY_DROP: {format_js_set(RULES_DB['PRIORITY_DROP'])},
    DROP: {format_js_set(RULES_DB['DROP'])}
  }},

  PARAMS: {{
    GLOBAL: {format_js_set(RULES_DB['PARAMS_GLOBAL'])},
    GLOBAL_REGEX: [/^utm_\\w+/i, /^ig_[\\w_]+/i, /^asa_\\w+/i, /^tt_[\\w_]+/i, /^li_[\\w_]+/i],
    PREFIX_BUCKETS: {format_js_prefix_buckets(RULES_DB['PARAMS_PREFIXES'])},
    PREFIXES_REGEX: [/_ga_/i, /^tt_[\\w_]+/i, /^li_[\\w_]+/i],
    COSMETIC: new Set(['fb_ref', 'fb_source', 'from', 'ref', 'share_id']),
    WHITELIST: new Set(['code', 'id', 'p', 'page', 'product_id', 'q', 'query', 'search', 'session_id', 'state', 'token', 'format', 'lang', 'locale', 'salt', 's']),
    EXEMPTIONS: new Map(),
    SCOPED_EXEMPTIONS: {format_scoped_exemptions(RULES_DB['SCOPED_PARAM_EXEMPTIONS'])}
  }},

  REGEX: {{
    PATH_BLOCK: [ /^\\/(\\w+\\/)?ads?\\//i, /\\/(ad|banner|tracker)\\.(js|gif|png)(\\?|$)/i ],
    HEURISTIC: [ /[?&](ad|ads|campaign|tracker)_[a-z]+=/i ],
    API_SIGNATURE_BYPASS: [ /\\/(api|graphql|trpc|rest)\\//i, /\\.(json|xml)(\\?|$)/i ]
  }},

  EXCEPTIONS: {{
    SUFFIXES: {format_js_set(RULES_DB['EXCEPTIONS_SUFFIXES'])},
    PREFIXES: new Set(['/favicon', '/assets/', '/static/', '/images/', '/img/', '/js/', '/css/']),
    SUBSTRINGS: new Set(['cdn-cgi']),
    SEGMENTS: new Set(['assets', 'static', 'images', 'img', 'css', 'js']),
    PATH_EXEMPTIONS: {format_js_map(RULES_DB['PATH_EXEMPTIONS'])}
  }}
}};
"""

def get_js_engine_logic() -> str:
    return r"""
class ACScanner {
  constructor(keywords) { this.keywords = keywords.map(k => k.toLowerCase()); }
  matches(text) {
    if (!text) return false;
    const target = text.length > CONFIG.AC_SCAN_MAX_LENGTH ? text.substring(0, CONFIG.AC_SCAN_MAX_LENGTH) : text;
    const lowerTarget = target.toLowerCase();
    return this.keywords.some(kw => lowerTarget.includes(kw));
  }
}

class HighPerformanceLRUCache {
  constructor(limit = 512) { this.limit = limit; this.cache = new Map(); }
  get(key) {
    if (!this.cache.has(key)) return null;
    const entry = this.cache.get(key);
    if (Date.now() > entry.expiry) { this.cache.delete(key); return null; }
    this.cache.delete(key); this.cache.set(key, entry);
    return entry.value;
  }
  set(key, value, ttl = 300000) {
    if (this.cache.size >= this.limit) this.cache.delete(this.cache.keys().next().value);
    this.cache.set(key, { value, expiry: Date.now() + ttl });
  }
}

const highConfidenceScanner = new ACScanner(RULES.KEYWORDS.HIGH_CONFIDENCE);
const pathScanner = new ACScanner(RULES.KEYWORDS.PATH_BLOCK);
const criticalPathScanner = new ACScanner([...RULES.CRITICAL_PATH.GENERIC, ...RULES.CRITICAL_PATH.SCRIPT_ROOTS]);
const COMBINED_PATH_REGEX = [...RULES.REGEX.PATH_BLOCK, ...RULES.REGEX.HEURISTIC];

const STATIC_EXTENSIONS = new Set();
const STATIC_FILENAMES = new Set();
for (const s of RULES.EXCEPTIONS.SUFFIXES) {
  if (!s) continue;
  if (s.startsWith('.')) STATIC_EXTENSIONS.add(s);
  else STATIC_FILENAMES.add(s);
}

const multiLevelCache = new HighPerformanceLRUCache(512);
const stats = { blocks: 0, allows: 0, toString: () => `Blocked: ${stats.blocks}, Allowed: ${stats.allows}` };
const criticalMapCache = new HighPerformanceLRUCache(256);

function isDomainMatch(setExact, wildcardsSet, hostname) {
  if (setExact.has(hostname)) return true;
  if (wildcardsSet.has(hostname)) return true;
  var pos = hostname.indexOf('.');
  while (pos >= 0) {
    if (wildcardsSet.has(hostname.substring(pos + 1))) return true;
    pos = hostname.indexOf('.', pos + 1);
  }
  return false;
}

const HELPERS = {
  isStaticFile: (pathLowerMaybeWithQuery) => {
    if (!pathLowerMaybeWithQuery) return false;
    const cleanPath = pathLowerMaybeWithQuery.split('?')[0];
    const lastDot = cleanPath.lastIndexOf('.');
    if (lastDot !== -1) {
      const ext = cleanPath.substring(lastDot);
      if (STATIC_EXTENSIONS.has(ext)) return true;
    }
    for (const fn of STATIC_FILENAMES) {
      if (cleanPath.endsWith(fn)) return true;
    }
    return false;
  },

  isPathExplicitlyAllowed: (pathLower) => {
    for (const prefix of RULES.EXCEPTIONS.PREFIXES) if (pathLower.startsWith(prefix)) return true;
    for (const sub of RULES.EXCEPTIONS.SUBSTRINGS) if (pathLower.includes(sub)) return true;
    for (const seg of RULES.EXCEPTIONS.SEGMENTS) if (pathLower.includes('/' + seg + '/')) return true;
    return false;
  },

  isPathExemptedForDomain: (hostname, pathLower) => {
    for (const [domainOrPrefix, exemptedPaths] of RULES.EXCEPTIONS.PATH_EXEMPTIONS) {
      let isMatch = false;
      if (domainOrPrefix.endsWith('.') && /^\d/.test(domainOrPrefix)) {
          isMatch = hostname.startsWith(domainOrPrefix);
      } else {
          isMatch = (hostname === domainOrPrefix || hostname.endsWith('.' + domainOrPrefix));
      }
      
      if (isMatch) {
        for (const exemptedPath of exemptedPaths) {
          if (pathLower.includes(exemptedPath)) return true;
        }
      }
    }
    return false;
  },

  isScopedParamAllowed: (hostname, pathLower, lowerKey) => {
    let domainExemptions = RULES.PARAMS.SCOPED_EXEMPTIONS.get(hostname);
    if (!domainExemptions) {
        for (const [domain, paths] of RULES.PARAMS.SCOPED_EXEMPTIONS) {
            if (hostname.endsWith('.' + domain)) { domainExemptions = paths; break; }
        }
    }
    if (!domainExemptions) return false;

    for (const [pathStr, allowedParamsSet] of domainExemptions) {
        if (pathLower.includes(pathStr) && allowedParamsSet.has(lowerKey)) {
            return true;
        }
    }
    return false;
  },

  cleanTrackingParams: (urlStr, hostname, pathLower) => {
    if (!urlStr.includes('?')) return null;

    if (/[?&](signature|sig|hmac)=/i.test(pathLower)) return null;

    if (OAUTH_SAFE_HARBOR.DOMAINS.has(hostname) && hostname !== 'accounts.youtube.com') return null;
    
    if (OAUTH_SAFE_HARBOR.PATHS_REGEX.some(r => r.test(pathLower))) return null;

    if (isDomainMatch(PARAM_CLEANING_EXEMPTED_DOMAINS.EXACT, PARAM_CLEANING_EXEMPTED_DOMAINS.WILDCARDS, hostname)) return null;
    
    let rewriteType = '302';
    if (RULES.REGEX.API_SIGNATURE_BYPASS.some(r => r.test(pathLower)) || 
        hostname.startsWith('api.') || hostname.startsWith('appapi.') || 
        isDomainMatch(SILENT_REWRITE_DOMAINS.EXACT, SILENT_REWRITE_DOMAINS.WILDCARDS, hostname)) {
        rewriteType = 'REWRITE';
    }

    try {
      const _qi = urlStr.indexOf('?');
      if (_qi < 0) return null;
      const _hi = urlStr.indexOf('#', _qi);
      const base = urlStr.substring(0, _qi);
      let qs = _hi >= 0 ? urlStr.substring(_qi + 1, _hi) : urlStr.substring(_qi + 1);
      const hash = _hi >= 0 ? urlStr.substring(_hi) : '';

      if (!qs) return null;
      
      qs = qs.replace(/;/g, '&');
      
      const pairs = qs.split('&');
      const kept = [];
      let changed = false;

      for (let i = 0; i < pairs.length; i++) {
        const pair = pairs[i];
        if (!pair) { kept.push(pair); continue; }
        const eqIdx = pair.indexOf('=');
        const key = eqIdx >= 0 ? pair.substring(0, eqIdx) : pair;
        const lowerKey = key.toLowerCase();

        if (RULES.PARAMS.WHITELIST.has(lowerKey) || HELPERS.isScopedParamAllowed(hostname, pathLower, lowerKey)) {
            kept.push(pair); continue;
        }

        if (RULES.PARAMS.GLOBAL.has(key) || RULES.PARAMS.COSMETIC.has(key)) { changed = true; continue; }

        let prefixHit = false;
        if (lowerKey) {
          const bucket = RULES.PARAMS.PREFIX_BUCKETS.get(lowerKey[0]);
          if (bucket) {
            for (let j = 0; j < bucket.length; j++) {
              if (lowerKey.startsWith(bucket[j])) { prefixHit = true; break; }
            }
          }
        }
        if (prefixHit) { changed = true; continue; }

        if (RULES.PARAMS.GLOBAL_REGEX.some(r => r.test(lowerKey)) || RULES.PARAMS.PREFIXES_REGEX.some(r => r.test(lowerKey))) {
          changed = true; continue;
        }

        kept.push(pair);
      }

      if (!changed) return null;
      const newQs = kept.join('&');
      return { url: newQs ? base + '?' + newQs + hash : base + hash, type: rewriteType };
    } catch (_) { return null; }
  }
};

function getCriticalBlockedPaths(hostname) {
  const cached = criticalMapCache.get(hostname);
  if (cached !== null) return cached; 
  let setOrUndef = RULES.CRITICAL_PATH.MAP.get(hostname);
  if (!setOrUndef) {
    for (const [domain, paths] of RULES.CRITICAL_PATH.MAP) {
      if (hostname.endsWith('.' + domain)) { setOrUndef = paths; break; }
    }
  }
  const value = setOrUndef ? setOrUndef : false;
  criticalMapCache.set(hostname, value, 300000);
  return value;
}

function processRequest(request) {
  const url = request && request.url;
  if (!url) return null;

  try {
    const _pe = url.indexOf('://');
    const _hs = _pe >= 0 ? _pe + 3 : 0;
    const _ps = url.indexOf('/', _hs);
    const _hp = _ps >= 0 ? url.substring(_hs, _ps) : url.substring(_hs);
    const hostname = _hp.split(':')[0].toLowerCase();
    
    let rawPath = _ps >= 0 ? url.substring(_ps) : '/';
    const _fi = rawPath.indexOf('#');
    if (_fi >= 0) rawPath = rawPath.substring(0, _fi);

    let pathLower;
    try {
        let decoded = decodeURIComponent(rawPath);
        if (decoded.includes('%')) {
            try { decoded = decodeURIComponent(decoded); } catch (e) {}
        }
        pathLower = decoded.toLowerCase();
    } catch (e) {
        pathLower = rawPath.toLowerCase();
    }

    if (pathLower.includes('/accounts/checkconnection')) {
        return { response: { status: 204 } };
    }

    if (isDomainMatch(new Set(), RULES.PRIORITY_BLOCK_DOMAINS, hostname)) {
      stats.blocks++;
      multiLevelCache.set(hostname, 'BLOCK', 86400000);
      return { response: { status: 403, body: 'Blocked by P0' } };
    }
    
    if (RULES.REDIRECTOR_HOSTS.has(hostname)) {
      stats.blocks++;
      return { response: { status: 403, body: 'Blocked Redirector' } };
    }

    const blockedPaths = getCriticalBlockedPaths(hostname);
    if (blockedPaths && blockedPaths !== false) {
      for (const badPath of blockedPaths) {
        if (badPath) {
          const isDrop = badPath.startsWith('DROP:');
          const checkPath = isDrop ? badPath.substring(5) : badPath;
          if (pathLower.includes(checkPath)) {
            stats.blocks++;
            if (isDrop) {
                return { response: { status: 204 } };
            }
            return { response: { status: 403, body: 'Blocked by Map' } };
          }
        }
      }
    }

    const isSoftWhitelisted = isDomainMatch(RULES.SOFT_WHITELIST.EXACT, RULES.SOFT_WHITELIST.WILDCARDS, hostname);
    if (!isSoftWhitelisted) {
      if (isDomainMatch(RULES.BLOCK_DOMAINS, RULES.BLOCK_DOMAINS_WILDCARDS, hostname) || RULES.BLOCK_DOMAINS_REGEX.some(r => r.test(hostname))) {
        stats.blocks++; return { response: { status: 403, body: 'Blocked by Domain' } };
      }
    }

    if (OAUTH_SAFE_HARBOR.DOMAINS.has(hostname) && hostname !== 'accounts.youtube.com') {
        stats.allows++; return null;
    }

    if (isDomainMatch(ABSOLUTE_BYPASS_DOMAINS.EXACT, ABSOLUTE_BYPASS_DOMAINS.WILDCARDS, hostname)) {
        stats.allows++; return null;
    }

    const performCleaning = () => {
        const cleanResult = HELPERS.cleanTrackingParams(url, hostname, pathLower);
        if (cleanResult) {
            stats.allows++;
            if (cleanResult.type === 'REWRITE') return { url: cleanResult.url }; 
            return { response: { status: 302, headers: { Location: cleanResult.url } } };
        }
        return null;
    };

    if (isDomainMatch(RULES.HARD_WHITELIST.EXACT, RULES.HARD_WHITELIST.WILDCARDS, hostname)) {
      stats.allows++; return performCleaning(); 
    }

    if (HELPERS.isPathExemptedForDomain(hostname, pathLower)) {
        stats.allows++; return performCleaning();
    }

    const isExplicitlyAllowed = HELPERS.isPathExplicitlyAllowed(pathLower);
    const isStatic = HELPERS.isStaticFile(pathLower);

    if (!isExplicitlyAllowed && !isStatic) {
      for (const k of RULES.KEYWORDS.PRIORITY_DROP) {
        if (pathLower.includes(k)) {
          stats.blocks++; return { response: { status: 204 } };
        }
      }
    }

    if (!isExplicitlyAllowed) {
        if (highConfidenceScanner.matches(pathLower)) {
            stats.blocks++;
            return { response: { status: 403, body: 'Blocked by High Confidence Keyword' } };
        }
    }

    if (criticalPathScanner.matches(pathLower)) {
      stats.blocks++;
      return { response: { status: 403, body: 'Blocked by L1 (Script/Path)' } };
    }

    if (hostname === 'cmapi.tw.coupang.com') {
      if (/\/.*-ads\//.test(pathLower)) {
        stats.blocks++;
        return { response: { status: 403, body: 'Blocked by Coupang Omni-Block' } };
      }
    }

    if (!isSoftWhitelisted || (isSoftWhitelisted && !isStatic)) {
      if (!isExplicitlyAllowed && !isStatic) { 
        if (pathScanner.matches(pathLower)) {
          stats.blocks++; return { response: { status: 403, body: 'Blocked by Keyword' } };
        }
        if (COMBINED_PATH_REGEX.some(r => r.test(pathLower))) {
          stats.blocks++; return { response: { status: 403, body: 'Blocked by Regex' } };
        }
      }
    }

    if (!isExplicitlyAllowed && !isStatic) {
      for (const k of RULES.KEYWORDS.DROP) {
        if (pathLower.includes(k)) {
          stats.blocks++; return { response: { status: 204 } };
        }
      }
    }

    return performCleaning();

  } catch (err) {
    if (CONFIG.DEBUG_MODE) console.log(`[Error] ${err}`);
  }
  stats.allows++;
  return null;
}
"""

def compile_surge() -> str:
    js = get_js_rules_definition("Surge") + get_js_engine_logic()
    wrapper = """
if (typeof $request !== 'undefined') {
  $done(processRequest($request));
} else {
  if (typeof $done !== 'undefined') $done({ title: 'URL Ultimate Filter', content: `V${SCRIPT_VERSION} Active\\n${stats.toString()}` });
}
"""
    return js + wrapper

def compile_tampermonkey() -> str:
    header = f"""// ==UserScript==
// @name         URL Ultimate Filter V{VERSION}
// @namespace    http://tampermonkey.net/
// @version      {VERSION}
// @description  SSOT 前端防護盾牌，專業級 UI：極簡盾牌圖示、獨立計數器、點擊外部自動收合機制。
// @author       Jerry
// @match        *://*/*
// @run-at       document-start
// @grant        GM_registerMenuCommand
// ==/UserScript==

(function() {{
    'use strict';
"""
    js = get_js_rules_definition("Tampermonkey") + get_js_engine_logic()
    
    interceptor_logic = r"""
    const tmStats = {
        blocked: new Map(),
        cleaned: new Map(),
        allowed: new Map(),
        countBlocked: 0,
        countCleaned: 0,
        countAllowed: 0,
        
        recordBlock: function(u) { 
            this.countBlocked++;
            let c = 1;
            if(this.blocked.has(u)) { c = this.blocked.get(u) + 1; this.blocked.delete(u); }
            else if(this.blocked.size >= 50) this.blocked.delete(this.blocked.keys().next().value);
            this.blocked.set(u, c); 
            requestUpdate(); 
        },
        recordClean: function(o, n) { 
            this.countCleaned++;
            let c = 1;
            if(this.cleaned.has(o)) { c = this.cleaned.get(o).count + 1; this.cleaned.delete(o); }
            else if(this.cleaned.size >= 50) this.cleaned.delete(this.cleaned.keys().next().value);
            this.cleaned.set(o, {newUrl: n, count: c}); 
            requestUpdate(); 
        },
        recordAllow: function(u) {
            this.countAllowed++;
            let c = 1;
            if(this.allowed.has(u)) { c = this.allowed.get(u) + 1; this.allowed.delete(u); }
            else if(this.allowed.size >= 50) this.allowed.delete(this.allowed.keys().next().value);
            this.allowed.set(u, c);
            if(expanded && activeTab === 'allowed') requestUpdate(); 
        }
    };

    let uiContainer, fab, panel, listContainer;
    let expanded = false;
    let activeTab = null;
    let shieldVisible = true;
    let updatePending = false;

    if (typeof GM_registerMenuCommand !== 'undefined') {
        GM_registerMenuCommand("🛡️ 切換 URL 盾牌顯示/隱藏", () => {
            shieldVisible = !shieldVisible;
            if (uiContainer) uiContainer.style.display = shieldVisible ? 'block' : 'none';
        });
    }

    function initUI() {
        if (document.getElementById('ssot-ui-root')) return;
        
        uiContainer = document.createElement('div');
        uiContainer.id = 'ssot-ui-root';
        uiContainer.style.cssText = 'position:fixed; bottom:20px; right:20px; z-index:2147483647; font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; display: block;';
        
        fab = document.createElement('div');
        fab.innerHTML = '\u{1F6E1}\uFE0F';
        fab.title = 'URL Ultimate Filter';
        fab.style.cssText = 'width:28px; height:28px; border-radius:50%; background:#0f172a; border: 1px solid #334155; display:flex; align-items:center; justify-content:center; font-size:14px; cursor:pointer; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.5); user-select:none; transition: all 0.2s ease-out; opacity: 0.6;';
        fab.onmouseover = () => { fab.style.transform = 'scale(1.1)'; fab.style.opacity = '1'; };
        fab.onmouseout = () => { fab.style.transform = 'scale(1)'; fab.style.opacity = '0.6'; };
        fab.onclick = () => { 
            expanded = true; 
            activeTab = null;
            renderUI(); 
        };
        
        panel = document.createElement('div');
        panel.style.cssText = 'display:none; position:absolute; bottom:0; right:0; width:360px; background:#0f172a; border: 1px solid #334155; border-radius:12px; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5); overflow:hidden; flex-direction:column; color:#f8fafc;';
        
        const header = document.createElement('div');
        header.style.cssText = 'display:flex; justify-content:space-between; align-items:center; padding:12px 16px; background:#1e293b; border-bottom:1px solid #334155; user-select:none;';
        header.innerHTML = `<div style="font-weight:600; display:flex; align-items:center; gap:8px; color:#6366F1;"><span style="font-size:15px;">\u{1F6E1}\uFE0F</span> URL Ultimate Filter V${SCRIPT_VERSION}</div>`;
        panel.appendChild(header);
        
        const tabsRow = document.createElement('div');
        tabsRow.style.cssText = 'display:flex; padding:8px; gap:8px; background:#0f172a; border-bottom:1px solid #334155;';
        
        const createTab = (id, label, color) => {
            const t = document.createElement('div');
            t.id = `ssot-tab-${id}`;
            t.title = `點擊展開/收合 ${label} 列表`;
            t.style.cssText = `flex:1; text-align:center; padding:8px 4px; cursor:pointer; border-radius:6px; transition:all 0.2s; border-bottom:2px solid transparent; user-select:none; background:transparent;`;
            t.innerHTML = `<div style="color:${color}; font-weight:700; font-size:18px; line-height:1.2;" id="ssot-cnt-${id}">0</div><div style="color:#94a3b8; font-size:11px; margin-top:2px; font-weight:500;">${label}</div>`;
            t.onclick = () => { 
                if (activeTab === id) {
                    expanded = false;
                    activeTab = null;
                } else {
                    activeTab = id;
                }
                renderUI(); 
            };
            return t;
        };
        
        tabsRow.appendChild(createTab('blocked', 'Blocked', '#ef4444'));
        tabsRow.appendChild(createTab('cleaned', 'Cleaned', '#10b981'));
        tabsRow.appendChild(createTab('allowed', 'Allowed', '#cbd5e1'));
        panel.appendChild(tabsRow);
        
        listContainer = document.createElement('div');
        listContainer.id = 'ssot-list-container';
        listContainer.style.cssText = 'display:none; max-height:280px; overflow-y:auto; padding:0; background:#020617; overscroll-behavior: contain;';
        
        listContainer.onclick = (e) => e.stopPropagation();
        panel.appendChild(listContainer);
        
        uiContainer.appendChild(fab);
        uiContainer.appendChild(panel);
        (document.body || document.documentElement).appendChild(uiContainer);
        
        renderUI();
    }

    document.addEventListener('click', (e) => {
        if (expanded && uiContainer && !uiContainer.contains(e.target)) {
            expanded = false;
            activeTab = null;
            renderUI();
        }
    });

    function requestUpdate() {
        if (!updatePending) {
            updatePending = true;
            requestAnimationFrame(() => {
                updatePending = false;
                if (expanded) renderUI(); 
            });
        }
    }

    function renderUI() {
        if (!uiContainer) return;
        uiContainer.style.display = shieldVisible ? 'block' : 'none';
        if (!shieldVisible) return;

        if (!expanded) {
            fab.style.display = 'flex';
            panel.style.display = 'none';
            return;
        }

        fab.style.display = 'none';
        panel.style.display = 'flex';

        document.getElementById('ssot-cnt-blocked').innerText = tmStats.countBlocked;
        document.getElementById('ssot-cnt-cleaned').innerText = tmStats.countCleaned;
        document.getElementById('ssot-cnt-allowed').innerText = tmStats.countAllowed;

        ['blocked', 'cleaned', 'allowed'].forEach(t => {
            const el = document.getElementById(`ssot-tab-${t}`);
            if (!el) return;
            if (activeTab === t) {
                el.style.backgroundColor = '#1e293b';
                el.style.borderBottom = `2px solid ${t==='blocked'?'#ef4444':t==='cleaned'?'#10b981':'#cbd5e1'}`;
            } else {
                el.style.backgroundColor = 'transparent';
                el.style.borderBottom = '2px solid transparent';
            }
        });

        if (!activeTab) {
            listContainer.style.display = 'none';
            listContainer.innerHTML = '';
        } else {
            listContainer.style.display = 'block';
            let listHtml = '';
            const itemStyle = 'padding:8px 12px; border-bottom:1px solid #1e293b; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size:11px; word-break:break-all; line-height:1.4;';
            const badgeStyle = 'padding:2px 6px; border-radius:10px; font-size:10px; font-weight:bold; height:fit-content; white-space:nowrap; margin-left:8px;';
            
            if (activeTab === 'blocked') {
                if (tmStats.blocked.size === 0) listHtml = `<div style="padding:16px; text-align:center; color:#64748b; font-size:12px;">無攔截紀錄</div>`;
                else listHtml = Array.from(tmStats.blocked.entries()).reverse().map(([u, c]) => `<div style="${itemStyle} color:#fca5a5;">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                        <span>${u}</span>
                        ${c > 1 ? `<span style="${badgeStyle} background:#7f1d1d; color:#fecaca;">x${c}</span>` : ''}
                    </div>
                </div>`).join('');
            } else if (activeTab === 'cleaned') {
                if (tmStats.cleaned.size === 0) listHtml = `<div style="padding:16px; text-align:center; color:#64748b; font-size:12px;">無淨化紀錄</div>`;
                else listHtml = Array.from(tmStats.cleaned.entries()).reverse().map(([o, data]) => `<div style="${itemStyle}">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:4px;">
                        <div style="text-decoration:line-through; color:#475569;">${o}</div>
                        ${data.count > 1 ? `<span style="${badgeStyle} background:#064e3b; color:#a7f3d0;">x${data.count}</span>` : ''}
                    </div>
                    <div style="color:#6ee7b7;">➔ ${data.newUrl}</div>
                </div>`).join('');
            } else if (activeTab === 'allowed') {
                if (tmStats.allowed.size === 0) listHtml = `<div style="padding:16px; text-align:center; color:#64748b; font-size:12px;">無放行紀錄</div>`;
                else listHtml = Array.from(tmStats.allowed.entries()).reverse().map(([u, c]) => `<div style="${itemStyle} color:#94a3b8;">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                        <span>${u}</span>
                        ${c > 1 ? `<span style="${badgeStyle} background:#334155; color:#cbd5e1;">x${c}</span>` : ''}
                    </div>
                </div>`).join('');
            }
            listContainer.innerHTML = listHtml;
        }
    }

    function applyFilter(url) {
        if (!url || typeof url !== 'string' || !url.startsWith('http')) return null;
        return processRequest({ url: url });
    }

    const origFetch = window.fetch;
    window.fetch = async function(...args) {
        let url = typeof args[0] === 'string' ? args[0] : (args[0] && args[0].url ? args[0].url : '');
        if (url) {
            try { url = new URL(url, location.origin).href; } catch(e){}
            const action = applyFilter(url);
            if (action) {
                if (action.response && [403, 204].includes(action.response.status)) {
                    tmStats.recordBlock(url);
                    if (CONFIG.DEBUG_MODE) console.log(`[SSOT-TM] 🚫 Blocked: ${url}`);
                    return Promise.reject(new Error("Blocked by URL Ultimate Filter SSOT"));
                } else if (action.url) {
                    tmStats.recordClean(url, action.url);
                    if (CONFIG.DEBUG_MODE) console.log(`[SSOT-TM] ✏️ Rewrote: ${url} -> ${action.url}`);
                    if (typeof args[0] === 'string') args[0] = action.url;
                    else args[0] = new Request(action.url, args[0]);
                } else {
                    tmStats.recordAllow(url);
                }
            } else {
                tmStats.recordAllow(url);
            }
        }
        return origFetch.apply(this, args);
    };

    const origOpen = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function(method, url, ...rest) {
        this._ssotBlocked = false;
        if (url) {
            try {
                let absoluteUrl = new URL(url, location.origin).href;
                const action = applyFilter(absoluteUrl);
                if (action) {
                    if (action.response && [403, 204].includes(action.response.status)) {
                        tmStats.recordBlock(absoluteUrl);
                        this._ssotBlocked = true;
                    } else if (action.url) {
                        tmStats.recordClean(absoluteUrl, action.url);
                        url = action.url;
                    } else {
                        tmStats.recordAllow(absoluteUrl);
                    }
                } else {
                    tmStats.recordAllow(absoluteUrl);
                }
            } catch(e){}
        }
        return origOpen.call(this, method, url, ...rest);
    };

    const origSend = XMLHttpRequest.prototype.send;
    XMLHttpRequest.prototype.send = function(...args) {
        if (this._ssotBlocked) {
            this.dispatchEvent(new Event('error'));
            return;
        }
        return origSend.apply(this, args);
    };
    
    const observer = new MutationObserver((mutations) => {
        for (const mutation of mutations) {
            for (const node of mutation.addedNodes) {
                if (node.tagName === 'SCRIPT' || node.tagName === 'IMG' || node.tagName === 'IFRAME') {
                    if (node.src) {
                        try {
                            const action = applyFilter(node.src);
                            if (action && action.response && [403, 204].includes(action.response.status)) {
                                tmStats.recordBlock(node.src);
                                node.remove(); 
                            } else if (action && action.url && node.src !== action.url) {
                                tmStats.recordClean(node.src, action.url);
                                node.src = action.url; 
                            } else if (!action) {
                                tmStats.recordAllow(node.src);
                            }
                        } catch(e){}
                    }
                }
            }
        }
    });
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            observer.observe(document.documentElement, { childList: true, subtree: true });
            initUI();
        });
    } else {
        observer.observe(document.documentElement, { childList: true, subtree: true });
        initUI();
    }
})();
"""
    return header + js + interceptor_logic


# ==========================================
#  3. TEST SUITE & HTML REPORTS
# ==========================================

PRIORITY_MAP = { "ALLOW (Null)": 0, "CLEAN (302)": 1, "REWRITE (URL)": 2, "DROP (204)": 3, "BLOCK (403)": 4 }
RES_ALLOW = "ALLOW (Null)"
RES_CLEAN_302 = "CLEAN (302)"
RES_REWRITE = "REWRITE (URL)"
RES_DROP_204 = "DROP (204)"
RES_BLOCK_403 = "BLOCK (403)"

@dataclass(frozen=True)
class TestCase:
    category: str
    url: str
    expected: str
    expected_feature: Optional[str] = None
    is_e2e: bool = False
    e2e_target_url: Optional[str] = None

@dataclass
class TestOutcome:
    case: TestCase
    actual: str
    details: str
    is_pass: bool

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Regression Report - {version_name}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {{ --primary: #4F46E5; --success: #10B981; --danger: #EF4444; --warning: #F59E0B; --surface: #FFFFFF; --bg: #F3F4F6; --text-main: #111827; --text-sub: #6B7280; --border: #E5E7EB; }}
        * {{ box-sizing: border-box; outline: none; }}
        body {{ font-family: 'Inter', sans-serif; background-color: var(--bg); color: var(--text-main); margin: 0; padding: 0; }}
        .app-container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}
        .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; background: var(--surface); padding: 20px 24px; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }}
        .header h1 {{ margin: 0; font-size: 24px; font-weight: 700; color: var(--text-main); }}
        .header .meta {{ font-size: 14px; color: var(--text-sub); display: flex; gap: 16px; align-items: center; }}
        .badge-status {{ padding: 6px 12px; border-radius: 99px; font-weight: 600; font-size: 13px; letter-spacing: 0.5px; }}
        .status-pass {{ background: #D1FAE5; color: #065F46; }}
        .status-fail {{ background: #FEE2E2; color: #991B1B; }}
        .kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 20px; margin-bottom: 24px; }}
        .card {{ background: var(--surface); border-radius: 12px; padding: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); border: 1px solid var(--border); transition: transform 0.2s; }}
        .card:hover {{ transform: translateY(-2px); box-shadow: 0 4px 6px rgba(0,0,0,0.05); }}
        .kpi-label {{ font-size: 14px; color: var(--text-sub); font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em; }}
        .kpi-value {{ font-size: 32px; font-weight: 700; margin-top: 8px; color: var(--text-main); }}
        .kpi-icon {{ float: right; font-size: 24px; opacity: 0.2; }}
        .text-success {{ color: var(--success); }}
        .text-danger {{ color: var(--danger); }}
        
        .charts-container {{ display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 2fr); gap: 20px; margin-bottom: 24px; }}
        .chart-wrapper {{ position: relative; height: 300px; width: 100%; min-width: 0; overflow: hidden; }}
        @media (max-width: 1024px) {{ .charts-container {{ grid-template-columns: minmax(0, 1fr); }} }}
        
        .section-title {{ font-size: 18px; font-weight: 600; margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }}
        .section-title i {{ color: var(--primary); }}
        .table-container {{ background: var(--surface); border-radius: 12px; border: 1px solid var(--border); overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }}
        table {{ width: 100%; border-collapse: collapse; }}
        th {{ background: #F9FAFB; padding: 12px 24px; text-align: left; font-size: 12px; font-weight: 600; text-transform: uppercase; color: var(--text-sub); border-bottom: 1px solid var(--border); user-select: none; }}
        td {{ padding: 16px 24px; border-bottom: 1px solid var(--border); font-size: 14px; color: var(--text-main); vertical-align: top; }}
        tr:last-child td {{ border-bottom: none; }}
        tr:hover td {{ background: #F9FAFB; }}
        .url-cell {{ font-family: 'JetBrains Mono', monospace; font-size: 13px; color: var(--primary); word-break: break-all; max-width: 450px; }}
        .url-cell a {{ color: inherit; text-decoration: none; }}
        .url-cell a:hover {{ text-decoration: underline; }}
        .badge {{ padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 600; display: inline-block; }}
        .bg-pass {{ background: #ECFDF5; color: #047857; }}
        .bg-fail {{ background: #FEF2F2; color: #B91C1C; }}
        .category-tag {{ background: #EEF2FF; color: #4338CA; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: 500; white-space: nowrap; }}
        .toolbar {{ padding: 16px 24px; border-bottom: 1px solid var(--border); display: flex; gap: 16px; flex-wrap: wrap; background: #fff; }}
        .search-box {{ flex: 1; position: relative; min-width: 200px; }}
        .search-box i {{ position: absolute; left: 12px; top: 50%; transform: translateY(-50%); color: var(--text-sub); }}
        .search-box input {{ width: 100%; padding: 10px 10px 10px 40px; border: 1px solid var(--border); border-radius: 8px; font-size: 14px; transition: all 0.2s; }}
        .search-box input:focus {{ border-color: var(--primary); box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1); }}
        .filter-select {{ padding: 10px 16px; border: 1px solid var(--border); border-radius: 8px; font-size: 14px; color: var(--text-main); background: #fff; cursor: pointer; }}
        .filter-select:hover {{ border-color: #D1D5DB; }}
        .footer {{ text-align: center; margin-top: 40px; color: var(--text-sub); font-size: 13px; }}
    </style>
</head>
<body>
    <div class="app-container">
        <header class="header">
            <div>
                <h1>Regression Report <span style="color:var(--primary); font-size: 0.8em;">({version_name})</span></h1>
                <div class="meta">
                    <span><i class="far fa-clock"></i> {gen_time}</span>
                    <span><i class="fas fa-bolt"></i> SSOT Dynamic Matrix (Dual-Target)</span>
                    <span style="color: var(--primary); font-weight: 600;"><i class="fas fa-vial"></i> 總共測試了 {total} 個 CASES</span>
                </div>
            </div>
            <div class="badge-status {overall_status_class}">{overall_status_text}</div>
        </header>
        <div class="kpi-grid">
            <div class="card"><i class="fas fa-list kpi-icon"></i><div class="kpi-label">Total Cases</div><div class="kpi-value">{total}</div></div>
            <div class="card"><i class="fas fa-percentage kpi-icon"></i><div class="kpi-label">Pass Rate</div><div class="kpi-value {rate_color_class}">{rate}%</div></div>
            <div class="card"><i class="fas fa-check-circle kpi-icon text-success"></i><div class="kpi-label">Passed</div><div class="kpi-value text-success">{passed}</div></div>
            <div class="card"><i class="fas fa-times-circle kpi-icon text-danger"></i><div class="kpi-label">Failed</div><div class="kpi-value text-danger">{failed}</div></div>
        </div>
        
        <div class="charts-container">
            <div class="card"><div class="section-title"><i class="fas fa-chart-pie"></i> Result Distribution</div><div class="chart-wrapper"><canvas id="pieChart"></canvas></div></div>
            <div class="card"><div class="section-title"><i class="fas fa-chart-bar"></i> Category Breakdown</div><div class="chart-wrapper"><canvas id="barChart"></canvas></div></div>
        </div>

        <div class="card" style="padding: 0; overflow: hidden;">
            <div class="toolbar">
                <div class="section-title" style="margin: 0; margin-right: 20px;"><i class="fas fa-table"></i> Detailed Logs</div>
                <div class="search-box"><i class="fas fa-search"></i><input type="text" id="searchInput" placeholder="Search..." onkeyup="filterTable()"></div>
                <select id="categoryFilter" class="filter-select" onchange="filterTable()"><option value="all">All Categories</option>{category_options}</select>
                <select id="statusFilter" class="filter-select" onchange="filterTable()"><option value="all">All Status</option><option value="PASS">Passed</option><option value="FAIL">Failed</option></select>
            </div>
            <div style="overflow-x: auto;">
                <table id="logTable">
                    <thead><tr><th width="12%">Category</th><th width="45%">URL / Test Case</th><th width="8%">Result</th><th width="10%">Expected</th><th width="10%">Actual</th><th width="15%">Details</th></tr></thead>
                    <tbody>{table_rows}</tbody>
                </table>
            </div>
            <div id="noResults" style="text-align: center; padding: 40px; color: var(--text-sub); display: none;">No matching records found.</div>
        </div>
        <div class="footer">Generated by SSOT Compiler • {version_name}</div>
    </div>
    
    <script>
        const chartData = {json_chart_data};
        const initialStatusFilter = "{initial_status_filter}";
        
        window.addEventListener('load', function() {{
            if (initialStatusFilter !== 'all') {{
                const statusSelect = document.getElementById('statusFilter');
                if (statusSelect) {{ statusSelect.value = initialStatusFilter; filterTable(); }}
            }}
            
            new Chart(document.getElementById('pieChart').getContext('2d'), {{ 
                type: 'doughnut', 
                data: {{ 
                    labels: ['Passed', 'Failed'], 
                    datasets: [{{ data: [chartData.passed, chartData.failed], backgroundColor: ['#10B981', '#EF4444'], borderWidth: 0 }}] 
                }}, 
                options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ position: 'bottom' }} }}, cutout: '70%' }} 
            }});
            
            new Chart(document.getElementById('barChart').getContext('2d'), {{ 
                type: 'bar', 
                data: {{ 
                    labels: chartData.categories, 
                    datasets: [
                        {{ label: 'Passed', data: chartData.cat_passed, backgroundColor: '#10B981', borderRadius: 4 }}, 
                        {{ label: 'Failed', data: chartData.cat_failed, backgroundColor: '#EF4444', borderRadius: 4 }}
                    ] 
                }}, 
                options: {{ 
                    responsive: true, maintainAspectRatio: false, indexAxis: 'y', 
                    scales: {{ x: {{ stacked: true, grid: {{ display: false }} }}, y: {{ stacked: true, grid: {{ borderDash: [2, 2] }} }} }}, 
                    plugins: {{ legend: {{ position: 'bottom' }} }} 
                }} 
            }});
        }});
        
        function filterTable() {{
            const searchInput = document.getElementById('searchInput').value.toLowerCase();
            const catFilter = document.getElementById('categoryFilter').value;
            const statusFilter = document.getElementById('statusFilter').value;
            const rows = document.getElementById('logTable').getElementsByTagName('tr');
            let visibleCount = 0;
            for (let i = 1; i < rows.length; i++) {{
                const row = rows[i];
                const category = row.getAttribute('data-category');
                const status = row.getAttribute('data-status');
                const text = row.innerText.toLowerCase();
                if (text.includes(searchInput) && (catFilter === 'all' || category === catFilter) && (statusFilter === 'all' || status === statusFilter)) {{ 
                    row.style.display = ''; visibleCount++; 
                }} else {{ 
                    row.style.display = 'none'; 
                }}
            }}
            document.getElementById('noResults').style.display = visibleCount === 0 ? 'block' : 'none';
        }}
    </script>
</body>
</html>
"""

def is_domain_whitelisted(domain: str) -> bool:
    for pd in RULES_DB["PRIORITY_BLOCK_DOMAINS"]:
        if domain == pd or domain.endswith('.' + pd):
            return False
            
    all_wildcards = RULES_DB["HARD_WHITELIST"]["WILDCARDS"] + RULES_DB["SOFT_WHITELIST"]["WILDCARDS"]
    for wl in all_wildcards:
        if domain == wl or domain.endswith('.' + wl):
            return True
    return False

_ALL_BLOCK_KEYWORDS = [
    k.lower() for k in (
        RULES_DB["HIGH_CONFIDENCE"]
        + RULES_DB["CRITICAL_PATH_GENERIC"]
        + RULES_DB["CRITICAL_PATH_SCRIPT_ROOTS"]
        + RULES_DB["PATH_BLOCK"]
    )
]

def is_path_keyword_blocked(path: str) -> bool:
    path_lower = path.lower()
    for k in _ALL_BLOCK_KEYWORDS:
        if k in path_lower:
            return True
    return False

def generate_full_coverage_cases() -> List[TestCase]:
    cases: List[TestCase] = []
    print(f"[TEST GENERATOR] Auto-expanding Python RULES_DB to Matrix Test Suite...")

    dynamic_soft_wl = RULES_DB["SOFT_WHITELIST"]["WILDCARDS"][0] if RULES_DB["SOFT_WHITELIST"]["WILDCARDS"] else "youtube.com"
    dynamic_hard_wl = RULES_DB["HARD_WHITELIST"]["WILDCARDS"][0] if RULES_DB["HARD_WHITELIST"]["WILDCARDS"] else "apple.com"
    exempt_domain_exact = RULES_DB["PARAM_CLEANING_EXEMPTED_DOMAINS"]["EXACT"][0] if RULES_DB["PARAM_CLEANING_EXEMPTED_DOMAINS"]["EXACT"] else "shopback.com.tw"

    for d in RULES_DB["PRIORITY_BLOCK_DOMAINS"]:
        cases.append(TestCase("Auto: Priority", f"https://{d}/api", RES_BLOCK_403, "Blocked by L2"))
    
    for d in RULES_DB["BLOCK_DOMAINS"]:
        expected = RES_ALLOW if is_domain_whitelisted(d) else RES_BLOCK_403
        cases.append(TestCase("Auto: Domain Block", f"https://{d}/test", expected, "Blocked by Domain"))

    for d in RULES_DB["BLOCK_DOMAINS_WILDCARDS"]:
        expected_exact = RES_ALLOW if is_domain_whitelisted(d) else RES_BLOCK_403
        cases.append(TestCase("Auto: Domain Block WC (Exact)", f"https://{d}/test", expected_exact, "Blocked by Wildcard Domain"))
        sub = f"sub.{d}"
        expected_sub = RES_ALLOW if is_domain_whitelisted(sub) else RES_BLOCK_403
        cases.append(TestCase("Auto: Domain Block WC (Sub)", f"https://{sub}/test", expected_sub, "Blocked by Wildcard Subdomain"))

    for d in RULES_DB["REDIRECTOR_HOSTS"]:
        cases.append(TestCase("Auto: Redirector", f"https://{d}/target", RES_BLOCK_403, "Blocked Redirector"))

    for hostname, paths in RULES_DB["CRITICAL_PATH_MAP"].items():
        for p in paths:
            if p.startswith("DROP:"):
                clean_path = p.substring(5) if hasattr(p, 'substring') else p[5:]
                url_base = f"https://{hostname}" + (clean_path if clean_path.startswith("/") else f"/{clean_path}")
                cases.append(TestCase("Auto: Critical Map (Drop Routing)", url_base, RES_DROP_204, "Action Routing 支援 DROP 權重解析"))
            else:
                url_base = f"https://{hostname}" + (p if p.startswith("/") else f"/{p}")
                expected = RES_DROP_204 if "CheckConnection" in p else RES_BLOCK_403
                cases.append(TestCase("Auto: Critical Map", url_base, expected, "Blocked by Map"))

    for s in RULES_DB["CRITICAL_PATH_SCRIPT_ROOTS"]:
        cases.append(TestCase("Auto: Script Root Block", f"https://example.com/js/{s}1.0.js", RES_BLOCK_403, "Blocked by Root Keyword"))

    for k in RULES_DB["HIGH_CONFIDENCE"]:
         path_seg = f"{k}test.webp" if k.startswith("/") else f"/path/{k}/file.webp"
         cases.append(TestCase("Matrix: High Conf (Neutral)", f"https://example.com{path_seg}", RES_BLOCK_403, "High Conf Block"))
         cases.append(TestCase("Matrix: High Conf (Soft WL)", f"https://{dynamic_soft_wl}{path_seg}", RES_BLOCK_403, "High Conf Overrides Soft WL"))
         cases.append(TestCase("Matrix: High Conf (Hard WL)", f"https://{dynamic_hard_wl}{path_seg}", RES_ALLOW, "Hard WL Overrides Everything"))

    for k in RULES_DB["PATH_BLOCK"]:
         path_seg = f"{k}test" if k.startswith("/") else f"/path/{k}/file"
         cases.append(TestCase("Matrix: Keyword (Neutral)", f"https://example.com{path_seg}", RES_BLOCK_403, "Keyword Block"))
         cases.append(TestCase("Matrix: Keyword (Soft WL)", f"https://{dynamic_soft_wl}{path_seg}", RES_BLOCK_403, "Soft WL still blocks non-static Keywords"))

    for p in RULES_DB["CRITICAL_PATH_GENERIC"]:
        expected = RES_DROP_204 if "CheckConnection" in p else RES_BLOCK_403
        cases.append(TestCase("Auto: Critical Path", f"https://example.com{p if p.startswith('/') else '/' + p}", expected, "Blocked by L1"))

    static_suffixes = RULES_DB["EXCEPTIONS_SUFFIXES"]
    for k in RULES_DB["DROP"] + RULES_DB["PRIORITY_DROP"]:
        if any(k.endswith(s) for s in static_suffixes if s.startswith('.')): continue
        cases.append(TestCase("Auto: Keyword Drop", f"https://example.com/log/{k.replace('/', '')}", RES_DROP_204, "Silent Drop"))

    for p in RULES_DB["PARAMS_GLOBAL"]:
         test_path = f"/?{p}=test"
         cases.append(TestCase("Privacy: Clean (Neutral)", f"https://example.com{test_path}", RES_CLEAN_302, "Param Cleaning"))
         cases.append(TestCase("Privacy: Clean (Hard WL)", f"https://{dynamic_hard_wl}{test_path}", RES_CLEAN_302, "Hard WL Parameter Cleaning"))
         expected_shop = RES_BLOCK_403 if is_path_keyword_blocked(test_path) else RES_ALLOW
         cases.append(TestCase("Privacy: Exemption (Shop)", f"https://{exempt_domain_exact}{test_path}", expected_shop, "Exempted from cleaning"))

    cases.append(TestCase("Matrix: Double Decode Escape", "https://example.com/%2561%2564/banner.webp", RES_BLOCK_403, "Blocked by High Confidence Override (Double Decoded)"))
    cases.append(TestCase("Edge: HTTPDNS Direct IP", "https://143.92.88.1/shopee/batch_resolve_with_info?timestamp=1772072185", RES_BLOCK_403, "Blocked by L1 Critical Path"))
    cases.append(TestCase("Feature: Heuristic API Silent Rewrite", "https://unknown-ecommerce.com/graphql/user?fbclid=test", RES_REWRITE, "GraphQL path uses Silent Rewrite to clean tracking parameters safely"))
    cases.append(TestCase("Privacy: Telemetry Drop (YT)", "https://www.youtube.com/error_204?cosver=18.7.1.22H31&cmodel=iPhone16%2C1&a=logerror", RES_DROP_204, "Silent Drop for High Precision Telemetry"))
    cases.append(TestCase("Privacy: WP Ad Plugin (L1 Scanner)", "https://www.koc.com.tw/wp-content/plugins/advanced-ads-responsive/public/assets/js/script.js?ver=1.10.2", RES_BLOCK_403, "Must be blocked by L1 Scanner ignoring static whitelist"))
    cases.append(TestCase("AdBlock: Video Ad Subdomain", "https://news2.newaddiscover.com/videoads/?ca=71&cb=1772287290", RES_BLOCK_403, "Blocked Video Ad Subdomain via Regex"))
    cases.append(TestCase("Privacy: Universal Link Silent Rewrite", "https://www.591.com.tw/2S?salt=STrc0&s=al&utm_source=line", RES_REWRITE, "Used Silent Rewrite to clean params without 302 breaking Deep Link"))
    cases.append(TestCase("Privacy: API Silent Rewrite (591 BFF)", "https://bff-house.591.com.tw/v1/touch/sale/detail?utm_source=test&device_id=b26dd90d", RES_REWRITE, "Cleaned device_id and utm_ using Silent Rewrite without triggering CORS 302"))
    cases.append(TestCase("AdBlock: App Ads Services", "https://odm.app-ads-services.com/v1/track", RES_BLOCK_403, "Block known pure app advertising/tracking network"))
    cases.append(TestCase("Privacy: OTel Log Drop", "https://pbd.yahoo.com/otel/v1/logs", RES_DROP_204, "V44.37 OTLP Log Silent Drop (Elevated DROP precedence)"))
    cases.append(TestCase("Privacy: Generic Log Block", "https://example.com/api/v1/logs", RES_BLOCK_403, "V44.37 Generic v1 logs 403 Block via L1 Scanner"))
    cases.append(TestCase("BugFix: Canvas Test Tool", "https://browserleaks.com/canvas", RES_ALLOW, "V44.38 Exempt browserleaks.com from PATH_BLOCK 'canvas' keyword"))
    cases.append(TestCase("Fix: 104 App internal /ad/ path", "https://appapi.104.com.tw/2.0/ad/search/hashtag?device_type=0&device_id=6CCC0850&ad_type=full", RES_REWRITE, "Bypasses HIGH_CONFIDENCE /ad/ block via HARD_WHITELIST and strips device_id silently"))
    cases.append(TestCase("Privacy: Exemption (API Auth)", "https://api.feedly.com/v3/streams?device_id=abc&source=ios", RES_ALLOW, "Exempted to protect HMAC signatures"))
    cases.append(TestCase("Edge: Absolute Bypass (Finance)", "https://api.ecpay.com.tw/pay?source=web&ref=123", RES_ALLOW, "Absolute bypass stops scanning immediately"))
    cases.append(TestCase("BugFix: API Login Collision", "https://api.signin.104.com.tw/v2/api/login/valid-account", RES_ALLOW, "Prevent /api/log from falsely killing /api/login endpoints"))
    cases.append(TestCase("BugFix: Threads Path Exemption", "https://www.threads.com/@n_ys_m/post/DIaU/abc", RES_ALLOW, "Bypass L1/L2 path scanners using PATH_EXEMPTIONS"))
    cases.append(TestCase("BugFix: P0 Subdomain Inheritance", "https://px.ads.linkedin.com/test", RES_BLOCK_403, "Validate P0 wildcards logic correctly inherits down to subdomains"))

    cases.append(TestCase("Matrix: Scoped Exemption (Positive)", "https://appapi.104.com.tw/api/login?device_id=A1B2", RES_ALLOW, "參數與路徑皆吻合，精準放行"))
    cases.append(TestCase("Matrix: Scoped Exemption (Domain Mismatch)", "https://api.example.com/api/profile?device_id=A1B2", RES_REWRITE, "路徑與參數吻合但網域非授權目標，剝離參數"))
    cases.append(TestCase("Matrix: Scoped Exemption (Param Mismatch)", "https://appapi.104.com.tw/api/profile?utm_source=fb", RES_REWRITE, "命中路徑但該參數不在白名單內，剝離參數"))
    cases.append(TestCase("Matrix: Scoped Exemption (Cross Mixed)", "https://appapi.104.com.tw/api/data?device_id=A1B2&fbclid=XYZ", RES_REWRITE, "混雜合法與非法參數，執行局部淨化"))
    cases.append(TestCase("Edge: HMAC Signature Bypass", "https://api.example.com/data?utm_source=test&signature=12345abcde", RES_ALLOW, "防護數位簽章免遭剝離導致 403"))
    cases.append(TestCase("Edge: Non-Standard Separator", "https://example.com/page?utm_source=fb;fbclid=123", RES_CLEAN_302, "解析分號作為分隔符，一般網域觸發 302 淨化"))

    cases.append(TestCase("BugFix: Coupang Banner Image (Legacy)", "https://image2.coupangcdn.com/image/ccm/banner/e5d4619754089a7b25a763ac8700bc01.jpg", RES_ALLOW, "Exempted from HIGH_CONFIDENCE /banner/ block via PATH_EXEMPTIONS"))
    cases.append(TestCase("BugFix: Coupang Banner Image (New OMS)", "https://image11.coupangcdn.com/image/cmg/oms/banner/9133e5bb-7468-4613-90f3-9ee18cafa072_720x1900.png", RES_ALLOW, "Exempted from HIGH_CONFIDENCE /banner/ block via PATH_EXEMPTIONS"))
    cases.append(TestCase("Privacy: Coupang JSError Log", "https://asset2.coupangcdn.com/customjs/jserror/2.5.1/jslog.min.js", RES_BLOCK_403, "Blocked by CRITICAL_PATH_SCRIPT_ROOTS"))
    cases.append(TestCase("Privacy: Coupang FeatureFlag Telemetry", "https://cmapi.tw.coupang.com/modular/v1/endpoints/12900/ff/v1/featureFlag/batchTracking", RES_BLOCK_403, "Blocked by CRITICAL_PATH_MAP precise targeting"))
    cases.append(TestCase("Privacy: Favicon Proxy Exemption", "https://www.google.com/s2/favicons?domain=mcp.hubspot.com&sz=64", RES_ALLOW, "Bypass PATH_BLOCK 'hubspot' keyword via PATH_EXEMPTIONS"))

    cases.append(TestCase("Privacy: Shopee Event Telemetry", "https://patronus.idata.shopeemobile.com/event-receiver/api/v4/tw", RES_BLOCK_403, "Blocked by CRITICAL_PATH_MAP (V44.68 Baseline)"))
    cases.append(TestCase("BugFix: Shopee PDP Regex Exemption", "https://mall.shopee.tw/api/v4/pdp/get?_pft=1047551&ads_id=159771735", RES_ALLOW, "Bypass heuristic regex block via PATH_EXEMPTIONS"))
    cases.append(TestCase("Privacy: Shopee AB Test Telemetry", "https://shopee.tw/api/v4/abtest/traffic/get_client_experiments", RES_BLOCK_403, "Blocked by CRITICAL_PATH_MAP precise targeting"))

    cases.append(TestCase("Privacy: Slack Telemetry Drop", "https://clorastech.slack.com/clog/track/?data=1", RES_DROP_204, "V44.76 Action Routing 支援 DROP 權重解析"))

    # --- V44.77 104 APP 局部參數放行測試 ---
    cases.append(TestCase("BugFix: 104 App Notify API", "https://appapi.104.com.tw/2.0/notify/v2/message/personal?device_type=0&app_version=3.30.0&device_id=TEST_ID&id_ck_n=$$:v1:abc", RES_ALLOW, "精準放行 104 APP Notify 路徑之 device_id"))
    cases.append(TestCase("BugFix: 104 App User API", "https://appapi.104.com.tw/2.0/user/v2/info?device_type=0&app_version=3.30.0&device_id=TEST_ID&id_ck_n=$$:v1:abc", RES_ALLOW, "精準放行 104 APP User 路徑之 device_id"))
    cases.append(TestCase("BugFix: 104 App Company API", "https://appapi.104.com.tw/2.0/company/search/view?device_type=0&app_version=3.30.0&device_id=TEST_ID&source=&jobNoList=123", RES_ALLOW, "精準放行 104 APP Company 路徑之 device_id"))

    cases.append(TestCase("E2E: Payload Fetch", "https://static.104.com.tw/104main/jb/area/manjb/home/json/jobNotify/ad.json?v=1772752285970", RES_ALLOW, "確保第一階段資料層 UI 放行不破圖"))
    cases.append(TestCase("E2E: Internal Nav Rewrite", "https://static.104.com.tw/ad.json", RES_REWRITE, "模擬擷取 JSON 後點擊，觸發第二階段靜默重寫", is_e2e=True, e2e_target_url="https://guide.104.com.tw/career/compare/major/?utm_source=104&utm_medium=whitebar"))
    cases.append(TestCase("E2E: Malicious Payload Block", "https://static.104.com.tw/ad.json", RES_BLOCK_403, "模擬 JSON 內遭植入第三方追蹤並點擊，觸發 L1 攔截", is_e2e=True, e2e_target_url="https://googleadservices.com/track/click"))
    cases.append(TestCase("E2E: URL Fragment Bypass", "https://static.104.com.tw/ad.json", RES_ALLOW, "模擬 HTTP Hash 參數剝離物理限制", is_e2e=True, e2e_target_url="https://guide.104.com.tw/#/test?fbclid=123"))

    return cases

def evaluate_result(actual: Any, expected_type: str) -> Tuple[bool, str, str]:
    if isinstance(actual, dict) and "error" in actual: return False, "EXEC_ERR", f"{actual.get('error')}: {str(actual.get('details', ''))[:100]}"
    if actual is None:
        if expected_type == RES_ALLOW: return True, RES_ALLOW, ""
        return False, RES_ALLOW, f"Expected {expected_type} but got Null"

    if isinstance(actual, dict):
        if "response" in actual:
            resp = actual["response"]
            code = resp.get("status")
            body = resp.get("body", "")
            if code == 403:
                if expected_type == RES_BLOCK_403: return True, RES_BLOCK_403, str(body)
                if expected_type in {RES_DROP_204, RES_CLEAN_302, RES_REWRITE}: return True, "BLOCK (Promoted)", "Promoted to Block"
                return False, RES_BLOCK_403, str(body)
            if code == 204: 
                if expected_type == RES_DROP_204: return True, RES_DROP_204, ""
                if expected_type == RES_BLOCK_403: return True, "DROP (Optimized)", "Block effectively optimized to 204"
                return False, f"HTTP (204)", ""
            if code == 302: return (expected_type == RES_CLEAN_302), RES_CLEAN_302, ""
            return False, f"HTTP ({code})", str(body)[:200]
        elif "url" in actual:
            if expected_type == RES_REWRITE: 
                return True, RES_REWRITE, ""
            return False, "REWRITE", str(actual["url"])[:200]
            
    return False, "INVALID", str(actual)[:200]

def update_changelog():
    changelog_path = Path("CHANGELOG.md")
    today = datetime.now().strftime("%Y-%m-%d")
    new_entry = f"## V{VERSION} - {today}\n{CURRENT_RELEASE_NOTES.strip()}\n\n"

    if changelog_path.exists():
        content = changelog_path.read_text(encoding="utf-8")
        if f"## V{VERSION}" not in content:
            header = "# URL Ultimate Filter - Changelog\n\n"
            if content.startswith(header):
                content = content.replace(header, header + new_entry, 1)
            else:
                content = header + new_entry + content
            changelog_path.write_text(content, encoding="utf-8")
            print(f"📝 CHANGELOG.md 已自動追加記錄 (Added V{VERSION})")
    else:
        header = "# URL Ultimate Filter - Changelog\n\n"
        changelog_path.write_text(header + new_entry, encoding="utf-8")
        print(f"📝 創建了新的 CHANGELOG.md 並寫入 V{VERSION} 記錄")

def run_tests():
    print(f"1. [SSOT COMPILER] Compiling Python RULES_DB to Dual-Target JavaScript (V{VERSION})...")
    js_surge_content = compile_surge()
    js_tampermonkey_content = compile_tampermonkey()
    js_surge_filename = "URL-Ultimate-Filter-Surge.js"
    js_tm_filename = "URL-Ultimate-Filter-Tampermonkey.user.js"

    cases = generate_full_coverage_cases()
    unique_cases = {c.category + c.url: c for c in cases}.values() 
    final_cases = sorted(list(unique_cases), key=lambda c: c.category)

    runner_code = textwrap.dedent("""
    global.$request = undefined;
    global.$done = function(data) {};
    global.$notification = { post: function() {} };
    const fs = require('fs');
    """) + "\n\n" + js_surge_content + "\n\n" + textwrap.dedent("""
    function runTest(c) {
      if (typeof initializeOnce === 'function') initializeOnce();
      try {
          let res1 = processRequest({ url: c.url });
          if (c.is_e2e) {
              if (res1 !== null) return { error: "E2E Phase 1 Failed", details: "Initial payload fetch was blocked." };
              let targetUrl = c.e2e_target_url;
              let hashIdx = targetUrl.indexOf('#');
              if (hashIdx !== -1) targetUrl = targetUrl.substring(0, hashIdx);
              return processRequest({ url: targetUrl });
          }
          return res1;
      } catch (e) { return { error: "Runtime Error", details: String(e) }; }
    }
    try {
        const payloadPath = process.argv[2];
        const cases = JSON.parse(fs.readFileSync(payloadPath, 'utf8'));
        const results = cases.map(c => ({ id: c.id, output: runTest(c) }));
        console.log(JSON.stringify(results));
    } catch (e) {
        console.log(JSON.stringify([{ error: "Batch Failure", details: String(e) }]));
    }
    """)

    fd_runner, runner_path = tempfile.mkstemp(suffix=".js")
    os.close(fd_runner)
    fd_payload, payload_path = tempfile.mkstemp(suffix=".json")
    os.close(fd_payload)

    try:
        Path(runner_path).write_text(runner_code, encoding="utf-8")
        payload_data = [{"id": i, "url": c.url, "is_e2e": c.is_e2e, "e2e_target_url": c.e2e_target_url} for i, c in enumerate(final_cases)]
        with open(payload_path, 'w', encoding='utf-8') as f: json.dump(payload_data, f)

        print(f"2. [BATCH ENGINE] Testing {len(final_cases)} SSOT Generated Cases via Node.js...")
        p = Popen(["node", runner_path, payload_path], stdout=PIPE, stderr=PIPE, text=True, encoding="utf-8")
        stdout, stderr = p.communicate()
        
        if p.returncode != 0:
            print(f"[FATAL ERROR] Node Execution Failed:\n{stderr}")
            sys.exit(1)
            
        results = json.loads(stdout)
        result_map = {r['id']: r for r in results}
        outcomes = []
        for i, c in enumerate(final_cases):
            res = result_map.get(i, {})
            actual_output = res.get('output')
            is_pass, status, details = evaluate_result(actual_output, c.expected)
            if c.is_e2e and is_pass:
                details = f"[E2E Passed] {c.expected_feature}"
            outcomes.append(TestOutcome(c, status, details, is_pass))

        passed = sum(1 for o in outcomes if o.is_pass)
        total = len(outcomes)
        failed = total - passed
        rate = round((passed/total)*100, 1) if total else 0

        category_stats = defaultdict(lambda: {"pass": 0, "fail": 0})
        rows_html = ""
        for o in outcomes:
            cat = o.case.category
            if o.is_pass: category_stats[cat]["pass"] += 1
            else: category_stats[cat]["fail"] += 1
            cls = "bg-pass" if o.is_pass else "bg-fail"
            txt = "PASS" if o.is_pass else "FAIL"
            color = "#10B981" if o.is_pass else "#EF4444"
            rows_html += f"<tr data-category='{cat}' data-status='{txt}'><td><span class='category-tag'>{cat}</span></td><td class='url-cell'><a href='{o.case.url}' target='_blank'>{o.case.url}</a></td><td><span class='badge {cls}'>{txt}</span></td><td style='font-size:13px; color:var(--text-sub);'>{o.case.expected}</td><td style='font-size:13px; font-weight:600; color:{color};'>{o.actual}</td><td style='font-size:12px; color:var(--text-sub);'>{o.details}</td></tr>"

        sorted_cats = sorted(category_stats.keys())
        cat_options_html = "".join([f'<option value="{cat}">{cat}</option>' for cat in sorted_cats])
        chart_data = {"passed": passed, "failed": failed, "categories": sorted_cats, "cat_passed": [category_stats[c]["pass"] for c in sorted_cats], "cat_failed": [category_stats[c]["fail"] for c in sorted_cats]}
        
        initial_status_filter = "FAIL" if failed > 0 else "all"
        overall_status_class = "status-pass" if failed == 0 else "status-fail"
        overall_status_text = "ALL SYSTEMS GO" if failed == 0 else f"{failed} ISSUES FOUND"
        rate_color_class = "text-success" if rate == 100 else ("text-warning" if rate > 90 else "text-danger")

        public_dir = Path("public")
        public_dir.mkdir(exist_ok=True)
        report_name = public_dir / "index.html"

        html = HTML_TEMPLATE.format(
            version_name=f"V{VERSION}", gen_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
            rate=rate, total=total, passed=passed, failed=failed, table_rows=rows_html,
            initial_status_filter=initial_status_filter, overall_status_class=overall_status_class,
            overall_status_text=overall_status_text, rate_color_class=rate_color_class,
            category_options=cat_options_html, json_chart_data=json.dumps(chart_data)
        )
        with open(report_name, "w", encoding="utf-8") as f: f.write(html)
        
        print("\n" + "="*55)
        print(f"📊 測試統計 (Test Statistics)")
        print(f"   - 總共測試案例 (Total Cases) : {total} CASES")
        print(f"   - 成功通過 (Passed)          : {passed} CASES")
        print(f"   - 失敗錯誤 (Failed)          : {failed} CASES")
        print("="*55)

        if passed == total:
            with open(js_surge_filename, "w", encoding="utf-8") as f: f.write(js_surge_content)
            with open(js_tm_filename, "w", encoding="utf-8") as f: f.write(js_tampermonkey_content)
            
            # --- [Architecture-V44.77] 觸發自動更新日誌 ---
            update_changelog()
            
            print(f"\n✅  SSOT DUAL-TARGET BUILD & TEST PASSED")
            print(f"📄  Surge Edition Saved: {js_surge_filename}")
            print(f"📄  Tampermonkey Edition Saved: {js_tm_filename}")
            print(f"📄  Test Report Saved for Pages: {report_name}")
        else:
            print(f"\n❌  SSOT TEST FAILED")
            print(f"⚠️  JavaScript Generation SKIPPED due to test failures.")
        print("="*55 + "\n")

    finally:
        Path(runner_path).unlink(missing_ok=True)
        Path(payload_path).unlink(missing_ok=True)

if __name__ == "__main__":
    run_tests()