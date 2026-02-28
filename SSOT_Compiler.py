#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
URL Ultimate Filter - V44.20 SSOT Compiler & Matrix Test Suite
-------------------------
架構更新：
1. [Architecture] 引入 SSOT，規則資料庫轉移至 Python 端維護。
2. [Compiler] 實作 Pretty-Print 陣列排版引擎，恢復 JS 檔案多行可讀性。
3. [Privacy] 實作 PARAM_CLEANING_EXEMPTED_DOMAINS，保護電商返利與歸因參數。
4. [Feature] 升級蝦皮追蹤子網域為 P0，防範軟白名單覆蓋；新增 HTTPDNS 攔截。
5. [Optimize-V44.16] 導入「啟發式 API 簽章防護機制 (Heuristic API Signature Bypass)」。
6. [Feature-V44.17] 建立 FINANCE_SAFE_HARBOR (金融避風港) 機制，將金融、第三方支付與政府憑證網域獨立。
7. [Fix-V44.18] 修正啟發式 API 引擎中 v\d+ (如 /v2/) 對標準網頁 (如 LINE Today) 造成的 False Positive 誤判。
8. [Privacy-V44.19] 針對 YouTube 等 App 的高精度設備指紋遙測 (如 /error_204, a=logerror) 實作全域靜默丟棄 (DROP 204)。
9. [Privacy-V44.20] 將 elads.kocpc.com.tw 納入 BLOCK_DOMAINS，精準封鎖第一方廣告追蹤腳本 (First-Party Tracking)。
"""

import json
import os
import sys
import tempfile
import textwrap
import csv
from datetime import datetime
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from subprocess import PIPE, Popen
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

VERSION = "44.20"

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
    "OAUTH_SAFE_HARBOR_PATHS": [
        '/oauth', '/oauth2', '/authorize', '/login', '/signin', '/session'
    ],
    "PARAM_CLEANING_EXEMPTED_DOMAINS": [
        'shopback.com.tw', 'extrabux.com', 'buy.line.me'
    ],
    "FINANCE_SAFE_HARBOR": {
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
            'post.gov.tw', 'nhi.gov.tw', 'mohw.gov.tw', 'org.tw', 'tdcc.com.tw'
        ]
    },
    "PRIORITY_BLOCK_DOMAINS": [
        'penphone92.com', 'api.penphone92.com', 'www.penphone92.com', 
        'cdn-path.com', 'www.cdn-path.com', 
        'mobile.events.data.microsoft.com', 'browser.events.data.microsoft.com', 'self.events.data.microsoft.com',
        'onecollector.cloudapp.aria.akadns.net', 'watson.telemetry.microsoft.com',
        'ad.impactify.io', 'ad.impactify.media', 'impactify.media',
        'firebaselogging-pa.googleapis.com', 'crashlyticsreports-pa.googleapis.com',
        's.360.cn', 'stat.360.cn', 'shouji.360.cn', 'browser.360.cn',
        'ping.sogou.com', 'pb.sogou.com', 'inte.sogou.com', 'lu.sogou.com',
        'hm.baidu.com', 'pos.baidu.com', 'wn.pos.baidu.com', 'sp0.baidu.com', 'sp1.baidu.com', 'sofire.baidu.com',
        'sm.cn', 'uczzd.cn', 'tanx.com', 'alimama.com', 'mmstat.com', 'ynuf.alipay.com',
        'uc.cn', 'ucweb.com', 'stat.quark.cn', 'unpm-upaas.quark.cn', 'cms-statistics.quark.cn',
        'mon.tiktokv.com', 'mon-va.tiktokv.com', 'log.tiktokv.com', 'log16-normal-c-useast1a.tiktokv.com',
        'ibytedtos.com', 'dc.shein.com', 'analysis.shein.com', 'st.shein.com', 'report.temu.com',
        'doorphone92.com', 'browser.sentry-cdn.com', 'adsv.omgrmn.tw', 'imasdk.googleapis.com', 'metrics.icloud.com', 'slackb.com',
        'applog.uc.cn', 'ecdmp.momoshop.com.tw', 'log.momoshop.com.tw', 'trk.momoshop.com.tw',
        'rtb.momoshop.com.tw', 'mercury.coupang.com', 'jslog.coupang.com',
        'ad.gamer.com.tw', 'ad-tracking.dcard.tw', 'b.bridgewell.com', 'scupio.com',
        'ad-geek.net', 'ad-hub.net', 'analysis.tw', 'cacafly.com', 'clickforce.com.tw', 'fast-trk.com',
        'funp.com', 'guoshipartners.com', 'imedia.com.tw', 'is-tracking.com', 'likr.tw', 'sitetag.us',
        'tagtoo.co', 'tenmax.io', 'trk.tw', 'urad.com.tw', 'vpon.com', 'ad-serv.teepr.com', 'appier.net', 'itad.linetv.tw',
        'sir90hl.com', 'uymgg1.com', 'easytomessage.com', 'caid.china-caa.org',
        'doubleclick.net', 'googleadservices.com', 'googlesyndication.com', 'admob.com', 'ads.google.com',
        'appsflyer.com', 'adjust.com', 'kochava.com', 'branch.io', 'app-measurement.com', 'singular.net',
        'unityads.unity3d.com', 'applovin.com', 'ironsrc.com', 'vungle.com', 'adcolony.com', 'chartboost.com',
        'tapjoy.com', 'pangle.io', 'taboola.com', 'outbrain.com', 'popads.net', 'ads.tiktok.com',
        'analytics.tiktok.com', 'ads.linkedin.com', 'ad.etmall.com.tw', 'ad.line.me', 'ad-history.line.me',
        'inmobi.com', 'inner-active.mobi', 'split.io', 'launchdarkly.com', 'clarity.ms', 'fullstory.com', 'cdn.segment.com',
        'dem.shopee.com', 'apm.tracking.shopee.tw', 'live-apm.shopee.tw', 'log-collector.shopee.tw', 'analytics.shopee.tw', 'dmp.shopee.tw'
    ],
    "REDIRECTOR_HOSTS": [
        '1ink.cc', 'adfoc.us', 'adsafelink.com', 'adshnk.com', 'adz7short.space', 'aylink.co',
        'bc.vc', 'bcvc.ink', 'birdurls.com', 'bitcosite.com', 'blogbux.net', 'boost.ink', 'ceesty.com',
        'clik.pw', 'clk.sh', 'clkmein.com', 'cllkme.com', 'corneey.com', 'cpmlink.net', 'cpmlink.pro',
        'cutpaid.com', 'destyy.com', 'dlink3.com', 'dz4link.com', 'earnlink.io', 'exe-links.com', 'exeo.app',
        'fc-lc.com', 'fc-lc.xyz', 'fcd.su', 'festyy.com', 'fir3.net', 'forex-trnd.com', 'gestyy.com',
        'getthot.com', 'gitlink.pro', 'gplinks.co', 'hotshorturl.com', 'icutlink.com', 'kimochi.info',
        'kingofshrink.com', 'linegee.net', 'link1s.com', 'linkmoni.com', 'linkpoi.me', 'linkshrink.net',
        'linksly.co', 'lnk2.cc', 'loaninsurehub.com', 'lolinez.com', 'mangalist.org', 'megalink.pro', 'met.bz',
        'miniurl.pw', 'mitly.us', 'noweconomy.live', 'oke.io', 'oko.sh', 'oni.vn', 'onlinefreecourse.net',
        'ouo.io', 'ouo.press', 'pahe.plus', 'payskip.org', 'pingit.im', 'realsht.mobi', 'rlu.ru', 'sh.st',
        'short.am', 'shortlinkto.biz', 'shortmoz.link', 'shrinkcash.com', 'shrt10.com', 'similarsites.com',
        'smilinglinks.com', 'spacetica.com', 'spaste.com', 'srt.am', 'stfly.me', 'stfly.xyz', 'supercheats.com',
        'swzz.xyz', 'techgeek.digital', 'techstudify.com', 'techtrendmakers.com', 'thinfi.com', 'thotpacks.xyz',
        'tmearn.net', 'tnshort.net', 'tribuntekno.com', 'turdown.com', 'tutwuri.id', 'uplinkto.hair',
        'urlbluemedia.shop', 'urlcash.com', 'urlcash.org', 'vinaurl.net', 'vzturl.com', 'xpshort.com', 'zegtrends.com'
    ],
    "HARD_WHITELIST": {
        "EXACT": [
            'iappapi.investing.com', 'cdn.oaistatic.com', 'files.oaiusercontent.com', 
            'claude.ai', 'gemini.google.com', 'perplexity.ai', 'www.perplexity.ai',
            'pplx-next-static-public.perplexity.ai', 'private-us-east-1.monica.im', 'api.felo.ai',
            'qianwen.aliyun.com', 'static.stepfun.com', 'api.openai.com', 'a-api.anthropic.com',
            'api.feedly.com', 'sandbox.feedly.com', 'cloud.feedly.com', 'translate.google.com', 'translate.googleapis.com',
            'inbox.google.com', 'reportaproblem.apple.com', 'accounts.google.com', 'appleid.apple.com', 'login.microsoftonline.com',
            'sso.godaddy.com', 'idmsa.apple.com', 'api.login.yahoo.com', 
            'firebaseappcheck.googleapis.com', 'firebaseinstallations.googleapis.com',
            'firebaseremoteconfig.googleapis.com', 'accounts.google.com.tw', 'accounts.felo.me',
            'api.etmall.com.tw',
            'tw.fd-api.com', 'tw.mapi.shp.yahoo.com', 
            'code.createjs.com', 'oa.ledabangong.com', 'oa.qianyibangong.com', 'raw.githubusercontent.com',
            'ss.ledabangong.com', 'userscripts.adtidy.org', 'api.github.com', 'api.vercel.com',
            'gateway.facebook.com', 'graph.instagram.com', 'graph.threads.net', 'i.instagram.com',
            'api.discord.com', 'api.twitch.tv', 'api.line.me', 'today.line.me',
            'pro.104.com.tw', 'datadog.pool.ntp.org', 'ewp.uber.com', 'copilot.microsoft.com', 
            'firebasedynamiclinks.googleapis.com', 'obs-tw.line-apps.com', 'obs.line-scdn.net'
        ],
        "WILDCARDS": [
            'sendgrid.net', 'agirls.aotter.net', 'query1.finance.yahoo.com', 'query2.finance.yahoo.com',
            'shopee.tw', 'mitake.com.tw', 'money-link.com.tw',
            'icloud.com', 'apple.com', 'whatsapp.net', 'update.microsoft.com', 'windowsupdate.com',
            'atlassian.net', 'auth0.com', 'okta.com', 'nextdns.io',
            'archive.is', 'archive.li', 'archive.ph', 'archive.today', 'archive.vn', 'cc.bingj.com',
            'perma.cc', 'timetravel.mementoweb.org', 'web-static.archive.org', 'web.archive.org',
            'googlevideo.com', 'app.goo.gl', 'goo.gl'
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
            'usiot.roborock.com', 'appapi.104.com.tw',
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
            'slack.com', 'feedly.com',
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
        'udp.yahoo.com', 'analytics.yahoo.com',
        'effirst.com', 'px.effirst.com', 'simonsignal.com', 
        'analysis.momoshop.com.tw', 'event.momoshop.com.tw', 'sspap.momoshop.com.tw',
        'analytics.etmall.com.tw', 'pixel.momoshop.com.tw', 'trace.momoshop.com.tw',
        'browser.sentry-cdn.com', 'bam.nr-data.net', 'bam-cell.nr-data.net', 'lrkt-in.com',
        'cdn.lr-ingest.com', 'r.lr-ingest.io', 'api-iam.intercom.io', 'openfpcdn.io', 'fingerprintjs.com',
        'fundingchoicesmessages.google.com', 'hotjar.com', 'segment.io', 'mixpanel.com', 'amplitude.com',
        'crazyegg.com', 'bugsnag.com', 'sentry.io', 'newrelic.com', 'logrocket.com', 'criteo.com',
        'pubmatic.com', 'rubiconproject.com', 'openx.com', 'fpjs.io', 'adunblock1.static-cloudflare.workers.dev',
        'guce.oath.com', 'app-site-association.cdn-apple.com', 'iadsdk.apple.com', 'cdn-edge-tracking.com',
        'edge-analytics.amazonaws.com', 'edge-telemetry.akamai.com', 'edge-tracking.cloudflare.com',
        'edgecompute-analytics.com', 'monitoring.edge-compute.io', 'realtime-edge.fastly.com', '2o7.net',
        'everesttech.net', 'log.felo.ai', 'event.sc.gearupportal.com', 'pidetupop.com', 'adform.net',
        'adsrvr.org', 'analytics.line.me', 'analytics.slashdotmedia.com', 'analytics.strava.com',
        'analytics.twitter.com', 'analytics.yahoo.com', 'api.pendo.io', 'c.clarity.ms', 'c.segment.com',
        'chartbeat.com', 'clicktale.net', 'clicky.com', 'comscore.com', 'criteo.net', 'customer.io',
        'data.investing.com', 'datadoghq.com', 'dynatrace.com', 'fullstory.com', 'heap.io', 'inspectlet.com',
        'iterable.com', 'keen.io', 'kissmetrics.com', 'loggly.com', 'matomo.cloud', 'mgid.com',
        'mouseflow.com', 'mparticle.com', 'mlytics.com', 'nr-data.net', 'oceanengine.com', 'openx.net',
        'optimizely.com', 'piwik.pro', 'posthog.com', 'quantserve.com', 'revcontent.com', 'rudderstack.com',
        'scorecardresearch.com', 'segment.com', 'semasio.net', 'snowplowanalytics.com', 'statcounter.com',
        'statsig.com', 'static.ads-twitter.com', 'sumo.com', 'sumome.com', 'tealium.com', 'track.hubspot.com',
        'track.tiara.daum.net', 'track.tiara.kakao.com', 'vwo.com', 'yieldlab.net', 'insight.linkedin.com',
        'px.ads.linkedin.com', 'fingerprint.com', 'doubleverify.com', 'iasds.com', 'moat.com', 'moatads.com',
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
        'youmi.net', 'zhugeio.com', 'adnext-a.akamaihd.net', 'appnext.hs.llnwd.net', 'fusioncdn.com',
        'toots-a.akamaihd.net', 'business.facebook.com', 'connect.facebook.net', 'graph.facebook.com',
        'events.tiktok.com', 'abema-adx.ameba.jp', 'ad.12306.cn', 'ad.360in.com', 'adroll.com', 'ads.yahoo.com',
        'adserver.yahoo.com', 'appnexus.com', 'bluekai.com', 'casalemedia.com', 'criteo.com', 'doubleclick.net',
        'googleadservices.com', 'googlesyndication.com', 'outbrain.com', 'taboola.com', 'rubiconproject.com',
        'pubmatic.com', 'openx.com', 'smartadserver.com', 'spotx.tv', 'yandex.ru', 'addthis.com', 'disqus.com',
        'onesignal.com', 'sharethis.com', 'bat.bing.com', 'clarity.ms', 'pinterest.com', 'reddit.com',
        'snapchat.com', 'elads.kocpc.com.tw'
    ],

    "CRITICAL_PATH_GENERIC": [
        '/accounts/CheckConnection', '/0.gif', '/1.gif', '/pixel.gif', '/beacon.gif', '/ping.gif',
        '/track.gif', '/dot.gif', '/clear.gif', '/empty.gif', '/shim.gif', '/spacer.gif', '/imp.gif',
        '/impression.gif', '/view.gif', '/sync.gif', '/sync.php', '/match.gif', '/match.php',
        '/utm.gif', '/event.gif', '/bk', '/bk.gif', '/collect', '/events',
        '/telemetry', '/metrics', '/traces', '/track', '/beacon', '/pixel', '/v1/collect', '/v1/events',
        '/v1/track', '/v1/telemetry', '/v1/metrics', '/v1/log', '/v1/traces', '/v1/report',
        '/appbase_report_log', '/stat_log', '/trackcode/', '/v2/collect', '/v2/events', '/v2/track',
        '/v2/telemetry', '/tp2', '/api/v1/collect', '/api/v1/events', '/api/v1/track', '/api/v1/telemetry',
        '/api/v1/log', '/api/log', '/v1/event', '/api/stats/ads', '/api/stats/atr', '/api/stats/qoe',
        '/api/stats/playback', '/pagead/gen_204', '/pagead/paralleladview', '/tiktok/pixel/events', 
        '/linkedin/insight/track', '/api/fingerprint', '/v1/fingerprint', '/cdn/fp/', '/api/collect', 
        '/api/track', '/tr/', '/beacon', '/api/v1/event', '/rest/n/log', '/action-log', 
        '/ramen/v1/events', '/_events', '/report/v1/log', '/app/mobilelog', '/api/web/ad/', 
        '/cdn/fingerprint/', '/api/device-id', '/api/visitor-id', '/ads/ga-audiences', '/doubleclick/', 
        '/google-analytics/', '/googleadservices/', '/googlesyndication/', '/googletagmanager/', 
        '/tiktok/track/', '/__utm.gif', '/j/collect', '/r/collect', '/api/batch', '/api/events', 
        '/api/logs/', '/api/v1/events', '/api/v1/track', '/api/v2/event', '/api/v2/events', '/collect?', 
        '/data/collect', '/events/track', '/ingest/', '/intake', '/p.gif', '/rec/bundle', '/t.gif', 
        '/telemetry/', '/track/', '/v1/pixel', '/v2/track', '/v3/track', '/2/client/addlog_batch', 
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
        'tracking.js', 'user-id.', 'user-timing.', 'wcslog.', 'jslog.min.', 'device-uuid.'
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
        'shopee.tw': ['/dataapi/dataweb/event/'],
        'api.tongyi.com': ['/qianwen/event/track'],
        'gw.alipayobjects.com': ['/config/loggw/'],
        'slack.com': ['/api/profiling.logging.enablement', '/api/telemetry'],
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
        'ad.360yield.com': [],
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
        'widget.intercom.io': [],
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
        'cmapi.tw.coupang.com': ['/featureflag/batchtracking', '/sdp-atf-ads/', '/sdp-btf-ads/', '/home-banner-ads/', '/category-banner-ads/', '/plp-ads/']
    },
    "HIGH_CONFIDENCE": [
        '/ad/', '/ads/', '/adv/', '/advert/', '/banner/', '/pixel/', '/tracker/', '/interstitial/', '/midroll/', '/popads/', '/preroll/', '/postroll/'
    ],
    "PATH_BLOCK": [
        'china-caa', '/advertising/', '/affiliate/',
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
        '/measurement', 'mp/collect', '/report/', '/reporting/', '/reports/', '/telemetry/',
        '/unstable/produce_batch', '/v1/produce', '/bugsnag/', '/crash/', 'debug/mp/collect', '/error/',
        '/envelope', '/exception/', '/stacktrace/', 'performance-tracking', 'real-user-monitoring',
        'web-vitals', 'audience', 'attribution', 'behavioral-targeting', 'cohort', 'cohort-analysis',
        'data-collection', 'data-sync', 'fingerprint', 'retargeting', 'session-replay', 'third-party-cookie',
        'user-analytics', 'user-behavior', 'user-cohort', 'user-segment', 'appier', 'comscore', 'fbevents',
        'fbq', 'google-analytics', 'onead', 'osano', 'sailthru', 'tapfiliate', 'utag.js', '/apmapi/',
        'canvas', 'webgl', 'audio-fp', 'font-detect'
    ],
    "DROP": [
        '.log', '?diag=', '?log=', '-log.', '/diag/', '/log/', '/logging/', '/logs/', 'adlog',
        'ads-beacon', 'airbrake', 'amp-analytics', 'batch', 'beacon', 'client-event', 'collect',
        'collect?', 'collector', 'crashlytics', 'csp-report', 'data-pipeline', 'error-monitoring',
        'error-report', 'heartbeat', 'ingest', 'intake', 'live-log', 'log-event', 'logevents',
        'loggly', 'log-hl', 'realtime-log', '/rum/', 'server-event', 'telemetry', 'uploadmobiledata',
        'web-beacon', 'web-vitals', 'crash-report', 'diagnostic.log', 'profiler', 'stacktrace', 'trace.json',
        '/error_204', 'a=logerror'
    ],
    "PARAMS_GLOBAL": [
        'dev_id', 'gclid', 'fbclid', 'ttclid', 'utm_source', 'utm_medium', 'utm_campaign', 'utm_term',
        'utm_content', 'yclid', 'mc_cid', 'mc_eid', 'srsltid', 'dclid', 'gclsrc', 'twclid', 'lid',
        '_branch_match_id', '_ga', '_gl', '_gid', '_openstat', 'admitad_uid', 'aiad_clid', 'awc', 'btag',
        'cjevent', 'cmpid', 'cuid', 'external_click_id', 'gad_source', 'gbraid', 'gps_adid', 'iclid',
        'igshid', 'irclickid', 'is_retargeting', 'ko_click_id', 'li_fat_id', 'mibextid', 'msclkid',
        'oprtrack', 'rb_clickid', 'sscid', 'trk', 'usqp', 'vero_conv', 'vero_id', 'wbraid', 'wt_mc',
        'xtor', 'ysclid', 'zanpid', 'yt_src', 'yt_ad', 's_kwcid', 'sc_cid'
    ],
    "EXCEPTIONS_SUFFIXES": [
        '.css', '.js', '.jpg', '.jpeg', '.gif', '.png', '.ico', '.svg', '.webp', '.woff', '.woff2', '.ttf',
        '.eot', '.mp4', '.mp3', '.mov', '.m4a', '.json', '.xml', '.yaml', '.yml', '.toml', '.ini',
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.zip', '.rar'
    ]
}

# ==========================================
#  2. JS COMPILER & FORMATTER (Pretty Print)
# ==========================================

def format_js_array(lst: List[str], indent: int = 4, items_per_line: int = 6) -> str:
    """將陣列排版為多行格式，恢復 800+ 行的美觀與高可讀性"""
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
    closing_indent = " " * (indent - 2)
    return f"new Map([\n{joined_entries}\n{closing_indent}])"

def compile_js() -> str:
    js_rules_definition = f"""/**
 * @file      URL-Ultimate-Filter-Surge.js
 * @version   {VERSION} (SSOT Compilation & Pages Deployment)
 * @description 
 * 1) [Architecture] Python SSOT 自動編譯生成。
 * 2) [Privacy] 加入 PARAM_CLEANING_EXEMPTED_DOMAINS 豁免清單，保護電商歸因。
 * 3) [Patch] 升級蝦皮遙測子網域為 P0 零信任層級，並於 L1 攔截 HTTPDNS 直連。
 * 4) [Optimize] 導入「啟發式 API 簽章防護機制 (Heuristic API Signature Bypass)」。
 * 5) [Feature] 新增 FINANCE_SAFE_HARBOR，全域絕對放行銀行、支付與政府網域，防範 302 破壞 POST 交易防護鏈。
 * 6) [Fix] 修正啟發式 API 引擎中 v\\d+ 對標準網頁造成的 False Positive 誤判。
 * 7) [Privacy-V44.19] 實作高精度設備指紋靜默丟棄 (DROP 204)，防護 /error_204 等遙測回傳機制。
 * 8) [Privacy-V44.20] 將 elads.kocpc.com.tw 納入 BLOCK_DOMAINS，精準封鎖第一方廣告追蹤腳本。
 * @lastUpdated {datetime.now().strftime("%Y-%m-%d")}
 */

const CONFIG = {{ DEBUG_MODE: false, AC_SCAN_MAX_LENGTH: 600 }};

const OAUTH_SAFE_HARBOR = {{
    DOMAINS: {format_js_set(RULES_DB['OAUTH_SAFE_HARBOR_DOMAINS'])},
    PATHS: {format_js_array(RULES_DB['OAUTH_SAFE_HARBOR_PATHS'])}
}};

const PARAM_CLEANING_EXEMPTED_DOMAINS = {format_js_set(RULES_DB['PARAM_CLEANING_EXEMPTED_DOMAINS'])};

const FINANCE_SAFE_HARBOR = {{
    EXACT: {format_js_set(RULES_DB['FINANCE_SAFE_HARBOR']['EXACT'])},
    WILDCARDS: {format_js_array(RULES_DB['FINANCE_SAFE_HARBOR']['WILDCARDS'])}
}};

// #################################################################################################
// #  ⚙️ RULES CONFIGURATION
// #################################################################################################

const RULES = {{
  PRIORITY_BLOCK_DOMAINS: {format_js_set(RULES_DB['PRIORITY_BLOCK_DOMAINS'])},
  REDIRECTOR_HOSTS: {format_js_set(RULES_DB['REDIRECTOR_HOSTS'])},

  HARD_WHITELIST: {{
    EXACT: {format_js_set(RULES_DB['HARD_WHITELIST']['EXACT'])},
    WILDCARDS: {format_js_array(RULES_DB['HARD_WHITELIST']['WILDCARDS'])}
  }},

  SOFT_WHITELIST: {{
    EXACT: {format_js_set(RULES_DB['SOFT_WHITELIST']['EXACT'])},
    WILDCARDS: {format_js_array(RULES_DB['SOFT_WHITELIST']['WILDCARDS'])}
  }},

  BLOCK_DOMAINS: {format_js_set(RULES_DB['BLOCK_DOMAINS'])},

  BLOCK_DOMAINS_REGEX: [
    /^ad[s]?\\d*\\.(ettoday\\.net|ltn\\.com\\.tw)$/i,
    /^(.+\\.)?sentry\\.io$/i,
    /^browser-intake-.*datadoghq\\.(com|eu|us)$/i,
    /^(.+\\.)?pidetupop\\.com$/i,
    /^(.+\\.)?cdn-net\\.com$/i,
    /^(.+\\.)?lr-ingest\\.io$/i,
    /^(.+\\.)?aotter\\.net$/i,
    /^(.+\\.)?ssp\\.yahoo\\.com$/i,
    /^(.+\\.)?pbs\\.yahoo\\.com$/i,
    /^(.+\\.)?ay\\.delivery$/i,
    /^(.+\\.)?cootlogix\\.com$/i,
    /^(.+\\.)?ottadvisors\\.com$/i
  ],

  CRITICAL_PATH: {{
    GENERIC: {format_js_array(RULES_DB['CRITICAL_PATH_GENERIC'])},
    SCRIPT_ROOTS: {format_js_array(RULES_DB['CRITICAL_PATH_SCRIPT_ROOTS'])},
    MAP: {format_js_map(RULES_DB['CRITICAL_PATH_MAP'])}
  }},

  KEYWORDS: {{
    HIGH_CONFIDENCE: {format_js_array(RULES_DB['HIGH_CONFIDENCE'])},
    PATH_BLOCK: {format_js_array(RULES_DB['PATH_BLOCK'])},
    DROP: {format_js_set(RULES_DB['DROP'])}
  }},

  PARAMS: {{
    GLOBAL: {format_js_set(RULES_DB['PARAMS_GLOBAL'])},
    GLOBAL_REGEX: [/^utm_\\w+/i, /^ig_[\\w_]+/i, /^asa_\\w+/i, /^tt_[\\w_]+/i, /^li_[\\w_]+/i],
    PREFIXES: new Set(['__cf_', '_bta', '_ga_', '_gat_', '_gid_', '_hs', '_oly_', 'action_', 'ad_', 'adjust_', 'aff_', 'af_', 'alg_', 'at_', 'bd_', 'bsft_', 'campaign_', 'cj', 'cm_', 'content_', 'creative_', 'fb_', 'from_', 'gcl_', 'guce_', 'hmsr_', 'hsa_', 'ir_', 'itm_', 'li_', 'matomo_', 'medium_', 'mkt_', 'ms_', 'mt_', 'mtm', 'pk_', 'piwik_', 'placement_', 'ref_', 'share_', 'source_', 'space_', 'term_', 'trk_', 'tt_', 'ttc_', 'vsm_', 'li_fat_', 'linkedin_']),
    PREFIXES_REGEX: [/_ga_/i, /^tt_[\\w_]+/i, /^li_[\\w_]+/i],
    COSMETIC: new Set(['fb_ref', 'fb_source', 'from', 'ref', 'share_id', 'spot_im_redirect_source']),
    WHITELIST: new Set(['code', 'id', 'item', 'p', 'page', 'product_id', 'q', 'query', 'search', 'session_id', 'state', 't', 'targetid', 'token', 'v', 'callback', 'ct', 'cv', 'filter', 'format', 'lang', 'locale', 'status', 'timestamp', 'type', 'withstats', 'access_token', 'client_assertion', 'client_id', 'device_id', 'nonce', 'redirect_uri', 'refresh_token', 'response_type', 'scope', 'direction', 'limit', 'offset', 'order', 'page_number', 'size', 'sort', 'sort_by', 'aff_sub', 'click_id', 'deal_id', 'offer_id', 'cancel_url', 'error_url', 'return_url', 'success_url', 'metadata', 'pagestatus', 'eventactiontype', 'unitpricewithdeliveryfee', 'previousitempricecount', 'optiontablelandingvendoritemid', 'selectedshowdeliverypddstatus']),
    EXEMPTIONS: new Map([
        ['www.google.com', new Set(['/maps/'])],
        ['taxi.sleepnova.org', new Set(['/api/v4/routes_estimate'])],
        ['cmapi.tw.coupang.com', new Set(['/'])],
        ['accounts.felo.me', new Set(['/'])],
        ['gcp-data-api.ltn.com.tw', new Set(['/'])]
    ])
  }},

  REGEX: {{
    PATH_BLOCK: [
      /^https?:\\/\\/[^\\/]+\\/(\\w+\\/)?ad[s]?\\//i,
      /\\.(com|net|org)\\/(\\w+\\/)?(ad|banner|tracker)\\.(js|gif|png)$/i,
      /\\/pagead\\/ads/i, /\\/googleads\\//i, /\\/ads\\/user-lists\\//i, /\\/marketing\\/api\\//i
    ],
    HEURISTIC: [
       /[?&](ad|ads|campaign|tracker)_[a-z]+=/i,
       /\\/ad(server|serve|vert|vertis|v)\\./i
    ],
    API_SIGNATURE_BYPASS: [
        /\\/(api|graphql|trpc|rest)\\//i, 
        /\\.(json|xml)(\\?|$)/i
    ]
  }},

  EXCEPTIONS: {{
    SUFFIXES: {format_js_set(RULES_DB['EXCEPTIONS_SUFFIXES'])},
    PREFIXES: new Set(['/favicon', '/assets/', '/static/', '/images/', '/img/', '/js/', '/css/', '/wp-content/', '/wp-includes/', '/fonts/', '/dist/', '/vendor/', '/public/']),
    SUBSTRINGS: new Set(['cdn-cgi', 'shop/goods', 'product/detail']),
    SEGMENTS: new Set(['assets', 'static', 'images', 'img', 'css', 'js', 'uploads', 'fonts', 'resources']),
    PATH_EXEMPTIONS: new Map([
        ['shopee.tw', new Set(['/api/v4/search/search_items'])],
        ['cmapi.tw.coupang.com', new Set(['/vendor-items/'])],
        ['www.google.com', new Set(['/url', '/search'])],
        ['play.googleapis.com', new Set(['/log/batch'])]
    ])
  }}
}};
"""

    js_engine_logic = r"""
class ACScanner {
  constructor(keywords) { this.keywords = keywords; }
  matches(text) {
    if (!text) return false;
    const target = text.length > CONFIG.AC_SCAN_MAX_LENGTH ? text.substring(0, CONFIG.AC_SCAN_MAX_LENGTH) : text;
    const lowerTarget = target.toLowerCase();
    return this.keywords.some(kw => lowerTarget.includes(kw));
  }
}

class HighPerformanceLRUCache {
  constructor(limit = 512) {
    this.limit = limit;
    this.cache = new Map();
  }
  get(key) {
    if (!this.cache.has(key)) return null;
    const entry = this.cache.get(key);
    if (Date.now() > entry.expiry) { this.cache.delete(key); return null; }
    this.cache.delete(key);
    this.cache.set(key, entry);
    return entry.value;
  }
  set(key, value, ttl = 300000) {
    if (this.cache.size >= this.limit) this.cache.delete(this.cache.keys().next().value);
    this.cache.set(key, { value, expiry: Date.now() + ttl });
  }
}

const highConfidenceScanner = new ACScanner(RULES.KEYWORDS.HIGH_CONFIDENCE);
const pathScanner = new ACScanner(RULES.KEYWORDS.PATH_BLOCK);
const criticalPathScanner = new ACScanner([
  ...RULES.CRITICAL_PATH.GENERIC,
  ...RULES.CRITICAL_PATH.SCRIPT_ROOTS
]);

const COMBINED_REGEX = [
  ...RULES.REGEX.PATH_BLOCK,
  ...RULES.REGEX.HEURISTIC,
  ...RULES.BLOCK_DOMAINS_REGEX
];

const PRIORITY_SUFFIX_LIST = Array.from(RULES.PRIORITY_BLOCK_DOMAINS);

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

const HELPERS = {
  isStaticFile: (pathLowerMaybeWithQuery) => {
    if (!pathLowerMaybeWithQuery) return false;
    const cleanPath = pathLowerMaybeWithQuery.split('?')[0].toLowerCase();
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
    const exemptedPaths = RULES.EXCEPTIONS.PATH_EXEMPTIONS.get(hostname);
    if (!exemptedPaths) return false;
    for (const exemptedPath of exemptedPaths) {
      if (pathLower.includes(exemptedPath)) return true;
    }
    return false;
  },

  isSafeHarborDomain: (hostname) => {
      if (hostname === 'accounts.youtube.com') return false; 
      return OAUTH_SAFE_HARBOR.DOMAINS.has(hostname);
  },

  isAuthPath: (pathLower) => {
      for (const keyword of OAUTH_SAFE_HARBOR.PATHS) {
          if (pathLower.includes(keyword)) return true;
      }
      return false;
  },

  cleanTrackingParams: (urlStr, hostname, pathLower) => {
    if (!urlStr.includes('?')) return null;

    if (HELPERS.isSafeHarborDomain(hostname) || HELPERS.isAuthPath(pathLower)) {
        return null;
    }

    if (PARAM_CLEANING_EXEMPTED_DOMAINS.has(hostname)) {
        return null;
    }
    
    if (RULES.REGEX.API_SIGNATURE_BYPASS.some(r => r.test(pathLower)) || hostname.startsWith('api.') || hostname.startsWith('graphql.')) {
        if (CONFIG.DEBUG_MODE) console.log(`[Exempted] Heuristic API Bypass: ${pathLower}`);
        return null;
    }

    const exemptions = RULES.PARAMS.EXEMPTIONS.get(hostname);
    if (exemptions) {
        for (const ex of exemptions) {
            if (pathLower.includes(ex)) return null; 
        }
    }

    try {
      const urlObj = new URL(urlStr);
      const params = urlObj.searchParams;
      let changed = false;

      for (const p of RULES.PARAMS.GLOBAL) {
        if (params.has(p)) { params.delete(p); changed = true; }
      }
      for (const p of RULES.PARAMS.COSMETIC) {
        if (params.has(p)) { params.delete(p); changed = true; }
      }

      const keys = Array.from(params.keys());
      for (const key of keys) {
        const lowerKey = key.toLowerCase();
        if (RULES.PARAMS.WHITELIST.has(lowerKey)) continue;
        for (const p of RULES.PARAMS.PREFIXES) {
          if (lowerKey.startsWith(p)) { params.delete(key); changed = true; break; }
        }
        if (!params.has(key)) continue;
        if (RULES.PARAMS.GLOBAL_REGEX.some(r => r.test(lowerKey)) ||
            RULES.PARAMS.PREFIXES_REGEX.some(r => r.test(lowerKey))) {
          params.delete(key);
          changed = true;
        }
      }
      return changed ? urlObj.toString() : null;
    } catch (_) {
      return null;
    }
  }
};

let __INITIALIZED__ = false;

function initializeOnce() {
  if (__INITIALIZED__) return;
  __INITIALIZED__ = true;
  FINANCE_SAFE_HARBOR.EXACT.forEach(d => multiLevelCache.set(d, 'ALLOW', 86400000));
  RULES.HARD_WHITELIST.EXACT.forEach(d => multiLevelCache.set(d, 'ALLOW', 86400000));
  RULES.PRIORITY_BLOCK_DOMAINS.forEach(d => multiLevelCache.set(d, 'BLOCK', 86400000));
}

function isDomainMatch(setExact, wildcards, hostname) {
  if (setExact.has(hostname)) return true;
  for (const d of wildcards) {
    if (hostname === d || hostname.endsWith('.' + d)) return true;
  }
  return false;
}

function isPriorityDomain(hostname) {
  if (RULES.PRIORITY_BLOCK_DOMAINS.has(hostname)) return true;
  for (const d of PRIORITY_SUFFIX_LIST) {
    if (hostname.endsWith('.' + d)) return true;
  }
  return false;
}

function getCriticalBlockedPaths(hostname) {
  const cached = criticalMapCache.get(hostname);
  if (cached !== null) return cached; 

  let setOrUndef = RULES.CRITICAL_PATH.MAP.get(hostname);

  if (!setOrUndef) {
    for (const [domain, paths] of RULES.CRITICAL_PATH.MAP) {
      if (hostname.endsWith('.' + domain)) {
        setOrUndef = paths;
        break;
      }
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
    const urlObj = new URL(url);
    const hostname = urlObj.hostname.toLowerCase();
    const rawPath = urlObj.pathname + urlObj.search;
    
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

    if (isPriorityDomain(hostname)) {
      stats.blocks++;
      multiLevelCache.set(hostname, 'BLOCK', 86400000);
      return { response: { status: 403, body: 'Blocked by P0 (Zero Trust)' } };
    }

    if (RULES.REDIRECTOR_HOSTS.has(hostname)) {
      stats.blocks++;
      return { response: { status: 403, body: 'Blocked Redirector' } };
    }

    const blockedPaths = getCriticalBlockedPaths(hostname);
    if (blockedPaths && blockedPaths !== false) {
      for (const badPath of blockedPaths) {
        if (badPath && pathLower.includes(badPath)) {
          stats.blocks++;
          if (CONFIG.DEBUG_MODE) console.log(`[Block] L4 Map: ${badPath}`);
          return { response: { status: 403, body: 'Blocked by Map' } };
        }
      }
    }

    if (HELPERS.isSafeHarborDomain(hostname)) {
        stats.allows++;
        return null;
    }

    if (isDomainMatch(FINANCE_SAFE_HARBOR.EXACT, FINANCE_SAFE_HARBOR.WILDCARDS, hostname)) {
      multiLevelCache.set(hostname, 'ALLOW', 86400000);
      stats.allows++;
      return null; 
    }

    const performCleaning = () => {
        const cleanUrl = HELPERS.cleanTrackingParams(url, hostname, pathLower);
        if (cleanUrl) {
            stats.allows++;
            return { response: { status: 302, headers: { Location: cleanUrl } } };
        }
        return null;
    };

    if (isDomainMatch(RULES.HARD_WHITELIST.EXACT, RULES.HARD_WHITELIST.WILDCARDS, hostname)) {
      multiLevelCache.set(hostname, 'ALLOW', 86400000);
      stats.allows++;
      return performCleaning(); 
    }

    const cached = multiLevelCache.get(hostname);
    if (cached === 'ALLOW') { 
        stats.allows++; 
        return performCleaning(); 
    }
    if (cached === 'BLOCK') { stats.blocks++; return { response: { status: 403, body: 'Blocked by Cache' } }; }

    if (HELPERS.isPathExemptedForDomain(hostname, pathLower)) {
        stats.allows++;
        return performCleaning();
    }

    const isExplicitlyAllowed = HELPERS.isPathExplicitlyAllowed(pathLower);
    const isStatic = HELPERS.isStaticFile(pathLower);
    const isSoftWhitelisted = isDomainMatch(RULES.SOFT_WHITELIST.EXACT, RULES.SOFT_WHITELIST.WILDCARDS, hostname);

    if (!isExplicitlyAllowed) {
        if (highConfidenceScanner.matches(pathLower)) {
            stats.blocks++;
            if (CONFIG.DEBUG_MODE) console.log(`[Block] High Confidence Override: ${pathLower}`);
            return { response: { status: 403, body: 'Blocked by High Confidence Keyword' } };
        }
    }

    if (criticalPathScanner.matches(pathLower)) {
      stats.blocks++;
      if (CONFIG.DEBUG_MODE) console.log(`[Block] L1 Critical: ${pathLower}`);
      return { response: { status: 403, body: 'Blocked by L1 (Script/Path)' } };
    }

    if (hostname === 'cmapi.tw.coupang.com') {
      if (/\/.*-ads\//.test(pathLower)) {
        stats.blocks++;
        return { response: { status: 403, body: 'Blocked by Coupang Omni-Block' } };
      }
    }

    if (!isSoftWhitelisted) {
      if (RULES.BLOCK_DOMAINS.has(hostname) || RULES.BLOCK_DOMAINS_REGEX.some(r => r.test(hostname))) {
        stats.blocks++;
        return { response: { status: 403, body: 'Blocked by Domain' } };
      }
    }

    if (!isSoftWhitelisted || (isSoftWhitelisted && !isStatic)) {
      if (!isExplicitlyAllowed && !isStatic) { 
        if (pathScanner.matches(pathLower)) {
          stats.blocks++;
          return { response: { status: 403, body: 'Blocked by Keyword' } };
        }
        if (COMBINED_REGEX.some(r => r.test(pathLower))) {
          stats.blocks++;
          return { response: { status: 403, body: 'Blocked by Regex' } };
        }
      }
    }

    if (!isExplicitlyAllowed && !isStatic) {
      for (const k of RULES.KEYWORDS.DROP) {
        if (pathLower.includes(k)) {
          stats.blocks++;
          return { response: { status: 204 } };
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

if (typeof $request !== 'undefined') {
  initializeOnce();
  $done(processRequest($request));
} else {
  if (typeof $done !== 'undefined') {
      $done({ title: 'URL Ultimate Filter', content: `V{VERSION} Active\n${stats.toString()}` });
  }
}
"""
    return js_rules_definition + js_engine_logic

# ==========================================
#  3. TEST SUITE & HTML REPORTS (SSOT DRIVEN)
# ==========================================

PRIORITY_MAP = { "ALLOW (Null)": 0, "CLEAN (302)": 1, "DROP (204)": 2, "BLOCK (403)": 3 }
RES_ALLOW = "ALLOW (Null)"
RES_CLEAN_302 = "CLEAN (302)"
RES_DROP_204 = "DROP (204)"
RES_BLOCK_403 = "BLOCK (403)"

@dataclass(frozen=True)
class TestCase:
    category: str
    url: str
    expected: str
    expected_feature: Optional[str] = None

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
                    <span><i class="fas fa-bolt"></i> SSOT Dynamic Matrix</span>
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
        <div class="footer">Generated by SSOT Compiler &bull; {version_name}</div>
    </div>
    
    <script>
        const chartData = {json_chart_data};
        const initialStatusFilter = "{initial_status_filter}";
        
        window.addEventListener('load', function() {{
            if (initialStatusFilter !== 'all') {{
                const statusSelect = document.getElementById('statusFilter');
                if (statusSelect) {{ statusSelect.value = initialStatusFilter; filterTable(); }}
            }}
            
            // Render Pie Chart
            new Chart(document.getElementById('pieChart').getContext('2d'), {{ 
                type: 'doughnut', 
                data: {{ 
                    labels: ['Passed', 'Failed'], 
                    datasets: [{{ data: [chartData.passed, chartData.failed], backgroundColor: ['#10B981', '#EF4444'], borderWidth: 0 }}] 
                }}, 
                options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ position: 'bottom' }} }}, cutout: '70%' }} 
            }});
            
            // Render Bar Chart
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
    """檢查黑名單網域是否實質上被白名單覆蓋，但須排除 P0 優先級阻擋。"""
    for pd in RULES_DB["PRIORITY_BLOCK_DOMAINS"]:
        if domain == pd or domain.endswith('.' + pd):
            return False
            
    all_wildcards = RULES_DB["HARD_WHITELIST"]["WILDCARDS"] + RULES_DB["SOFT_WHITELIST"]["WILDCARDS"]
    for wl in all_wildcards:
        if domain == wl or domain.endswith('.' + wl):
            return True
    return False

def is_path_keyword_blocked(path: str) -> bool:
    """模擬 JS L1/L2 關鍵字掃描器，判斷參數本身是否會觸發阻擋"""
    path_lower = path.lower()
    for k in RULES_DB["HIGH_CONFIDENCE"]:
        if k.lower() in path_lower: return True
    for k in RULES_DB["CRITICAL_PATH_GENERIC"] + RULES_DB["CRITICAL_PATH_SCRIPT_ROOTS"]:
        if k.lower() in path_lower: return True
    for k in RULES_DB["PATH_BLOCK"]:
        if k.lower() in path_lower: return True
    return False

def generate_full_coverage_cases() -> List[TestCase]:
    cases: List[TestCase] = []
    print(f"[TEST GENERATOR] Using Python RULES_DB as Single Source of Truth...")

    dynamic_soft_wl = RULES_DB["SOFT_WHITELIST"]["WILDCARDS"][0] if RULES_DB["SOFT_WHITELIST"]["WILDCARDS"] else "shopee.com"
    dynamic_hard_wl = RULES_DB["HARD_WHITELIST"]["WILDCARDS"][0] if RULES_DB["HARD_WHITELIST"]["WILDCARDS"] else "apple.com"
    oauth_domain = RULES_DB["OAUTH_SAFE_HARBOR_DOMAINS"][0] if RULES_DB["OAUTH_SAFE_HARBOR_DOMAINS"] else "accounts.google.com"
    exempt_domain = RULES_DB["PARAM_CLEANING_EXEMPTED_DOMAINS"][0] if RULES_DB["PARAM_CLEANING_EXEMPTED_DOMAINS"] else "shopback.com.tw"

    for d in RULES_DB["PRIORITY_BLOCK_DOMAINS"]:
        cases.append(TestCase("Auto: Priority", f"https://{d}/api", RES_BLOCK_403, "Blocked by L2"))
    
    for d in RULES_DB["BLOCK_DOMAINS"]:
        expected = RES_ALLOW if is_domain_whitelisted(d) else RES_BLOCK_403
        cases.append(TestCase("Auto: Domain Block", f"https://{d}/test", expected, "Blocked by Domain"))
        
    for d in RULES_DB["REDIRECTOR_HOSTS"]:
        cases.append(TestCase("Auto: Redirector", f"https://{d}/target", RES_BLOCK_403, "Blocked Redirector"))

    for hostname, paths in RULES_DB["CRITICAL_PATH_MAP"].items():
        for p in paths:
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
    for k in RULES_DB["DROP"]:
        if any(k.endswith(s) for s in static_suffixes if s.startswith('.')): continue
        cases.append(TestCase("Auto: Keyword Drop", f"https://example.com/log/{k.replace('/', '')}", RES_DROP_204, "Silent Drop"))

    for p in RULES_DB["PARAMS_GLOBAL"]:
         test_path = f"/?{p}=test"
         cases.append(TestCase("Privacy: Clean (Neutral)", f"https://example.com{test_path}", RES_CLEAN_302, "Param Cleaning"))
         cases.append(TestCase("Privacy: Clean (Hard WL)", f"https://{dynamic_hard_wl}{test_path}", RES_CLEAN_302, "Hard WL Parameter Cleaning"))
         
         expected_shop = RES_BLOCK_403 if is_path_keyword_blocked(test_path) else RES_ALLOW
         cases.append(TestCase("Privacy: Exemption (Shop)", f"https://{exempt_domain}{test_path}", expected_shop, "Exempted from cleaning"))
         
    cases.append(TestCase("Matrix: OAuth Safe Harbor", f"https://{oauth_domain}/oauth2/auth?gclid=123", RES_ALLOW, "OAuth bypasses everything"))
    cases.append(TestCase("Matrix: Double Decode Escape", "https://example.com/%2561%2564/banner.webp", RES_BLOCK_403, "Blocked by High Confidence Override (Double Decoded)"))
    cases.append(TestCase("Matrix: Triple Decode Perf Limit", "https://example.com/%252561%252564/banner.webp", RES_ALLOW, "Allowed (By Design - Perf Limit)"))

    cases.append(TestCase("Edge: Shopee DEM (P0)", "https://dem.shopee.com/dem/entrance/v1/apps/rw-platform/tags/web-performance/event/json", RES_BLOCK_403, "P0 bypasses Soft WL"))
    cases.append(TestCase("Edge: HTTPDNS Direct IP", "https://143.92.88.1/shopee/batch_resolve_with_info?timestamp=1772072185", RES_BLOCK_403, "Blocked by L1 Critical Path"))
    cases.append(TestCase("Feature: Heuristic API Bypass", "https://unknown-ecommerce.com/graphql/user?fbclid=test", RES_ALLOW, "GraphQL path exempted globally"))
    
    cases.append(TestCase("Finance: ECPay Post Data bypass", "https://payment.ecpay.com.tw/Cashier/AioCheckOut/V5?Token=test_token_123&TradeInfo=abc", RES_ALLOW, "Exempted from 302 to protect POST parameters"))
    cases.append(TestCase("Finance: Cathay Bank wildcard bypass", "https://ebank.cathaybk.com.tw/login?session_id=123&utm_source=should_not_clean", RES_ALLOW, "Exempted from 302 to protect token chain"))
    
    cases.append(TestCase("General: Web UI still cleans", "https://today.line.me/tw/v2/article/123?utm_source=line", RES_CLEAN_302, "Normal Hard Whitelist still undergoes parameter cleaning"))

    cases.append(TestCase("Privacy: Telemetry Drop (YT)", "https://www.youtube.com/error_204?cosver=18.7.1.22H31&cmodel=iPhone16%2C1&a=logerror", RES_DROP_204, "Silent Drop for High Precision Telemetry"))
    cases.append(TestCase("Privacy: Generic Logerror Drop", "https://example.com/api/tracking?a=logerror&device=iphone", RES_DROP_204, "Silent Drop for general a=logerror pattern"))
    
    # V44.20 新增 第一方廣告追蹤子網域測試
    cases.append(TestCase("Privacy: First-Party Ad", "https://elads.kocpc.com.tw/ktc/ktc.js/", RES_BLOCK_403, "Blocked First-Party Tracker"))

    return cases

# ==========================================
#  4. NODE BATCH ENGINE & EXECUTION
# ==========================================

def evaluate_result(actual: Any, expected_type: str) -> Tuple[bool, str, str]:
    if isinstance(actual, dict) and "error" in actual: return False, "EXEC_ERR", f"{actual.get('error')}: {str(actual.get('details', ''))[:100]}"
    if actual is None:
        if expected_type == RES_ALLOW: return True, RES_ALLOW, ""
        return False, RES_ALLOW, f"Expected {expected_type} but got Null"

    if isinstance(actual, dict) and "response" in actual:
        resp = actual["response"]
        code = resp.get("status")
        body = resp.get("body", "")
        if code == 403:
            if expected_type == RES_BLOCK_403: return True, RES_BLOCK_403, str(body)
            if expected_type in {RES_DROP_204, RES_CLEAN_302}: return True, "BLOCK (Promoted)", "Promoted to Block"
            return False, RES_BLOCK_403, str(body)
        if code == 204: return (expected_type == RES_DROP_204), RES_DROP_204, ""
        if code == 302: return (expected_type == RES_CLEAN_302), RES_CLEAN_302, ""
        return False, f"HTTP ({code})", str(body)[:200]
    return False, "INVALID", str(actual)[:200]

def run_tests():
    print(f"1. [SSOT COMPILER] Compiling Python RULES_DB to JavaScript (V{VERSION}) in memory...")
    js_content = compile_js()
    js_filename = "URL-Ultimate-Filter-Surge.js"

    cases = generate_full_coverage_cases()
    unique_cases = {c.url: c for c in cases}.values()
    final_cases = sorted(list(unique_cases), key=lambda c: c.category)

    runner_code = textwrap.dedent("""
    // --- Mock Surge Environment for Node.js ---
    global.$request = undefined;
    global.$done = function(data) {};
    global.$notification = { post: function() {} };
    const fs = require('fs');
    """) + "\n\n" + js_content + "\n\n" + textwrap.dedent("""
    // --- Batch Execution Engine ---
    function runTest(url) {
      var mockRequest = { url: url };
      if (typeof initializeOnce === 'function') initializeOnce();
      try { 
          return processRequest(mockRequest); 
      } catch (e) { 
          return { error: "Runtime Error", details: String(e) }; 
      }
    }
    
    try {
        const payloadPath = process.argv[2];
        const cases = JSON.parse(fs.readFileSync(payloadPath, 'utf8'));
        const results = cases.map(c => ({ id: c.id, output: runTest(c.url) }));
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
        payload_data = [{"id": i, "url": c.url} for i, c in enumerate(final_cases)]
        with open(payload_path, 'w', encoding='utf-8') as f: json.dump(payload_data, f)

        print(f"2. [BATCH ENGINE] Testing {len(final_cases)} SSOT Generated Cases via Node.js...")
        p = Popen(["node", runner_path, payload_path], stdout=PIPE, stderr=PIPE, text=True, encoding="utf-8")
        stdout, stderr = p.communicate()
        
        if p.returncode != 0:
            print(f"[FATAL ERROR] Node Execution Failed:\n{stderr}")
            sys.exit(1)
            
        results = json.loads(stdout)
        outcomes = []
        for i, c in enumerate(final_cases):
            res = next((r for r in results if r['id'] == i), {})
            actual_output = res.get('output')
            is_pass, status, details = evaluate_result(actual_output, c.expected)
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
        
        chart_data = {
            "passed": passed, "failed": failed, "categories": sorted_cats,
            "cat_passed": [category_stats[c]["pass"] for c in sorted_cats],
            "cat_failed": [category_stats[c]["fail"] for c in sorted_cats]
        }
        
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
        
        with open(report_name, "w", encoding="utf-8") as f: 
            f.write(html)
        
        print("\n" + "="*55)
        print(f"📊 測試統計 (Test Statistics)")
        print(f"   - 總共測試案例 (Total Cases) : {total} CASES")
        print(f"   - 成功通過 (Passed)          : {passed} CASES")
        print(f"   - 失敗錯誤 (Failed)          : {failed} CASES")
        print("="*55)

        if passed == total:
            with open(js_filename, "w", encoding="utf-8") as f:
                f.write(js_content)
            print(f"\n✅  SSOT BUILD & TEST PASSED")
            print(f"📄  JavaScript Compiled & Saved: {js_filename}")
            print(f"📄  Test Report Saved for Pages: {report_name}")
        else:
            print(f"\n❌  SSOT TEST FAILED")
            print(f"⚠️  JavaScript Generation SKIPPED due to test failures.")
            print(f"📄  Test Report Saved for Pages: {report_name}")
        print("="*55 + "\n")

    finally:
        Path(runner_path).unlink(missing_ok=True)
        Path(payload_path).unlink(missing_ok=True)

if __name__ == "__main__":
    run_tests()