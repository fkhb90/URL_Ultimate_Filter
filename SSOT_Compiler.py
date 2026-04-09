#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
URL Ultimate Filter - SSOT Compiler & Matrix Test Suite
-------------------------
當前版本：V45.33 (2026-04-09)
最新架構更新：
- [Compat] Grok App 登入修復：`xai.chronosphere.io` 加入 HARD_WHITELIST.EXACT，避免 OpenTelemetry 遙測端點被路徑規則誤殺導致 iOS Grok App 無法登入。

近期更新摘要 (完整歷史軌跡請參閱 CHANGELOG.md)：
- V45.33 (2026-04-09): Grok App 登入修復 — xai.chronosphere.io 加入 HARD_WHITELIST。
- V45.31 (2026-04-09): 新增 Surge REJECT-DROP 規則列表自動生成器 — DNS 層縱深防禦。
- V45.30 (2026-04-09): 微信公眾號遙測精準路徑攔截。
- V45.29 (2026-04-09): ChatGLM BDMS 追蹤像素靜默拋棄。
- V45.28 (2026-04-09): 中國推送 SDK 靜默拋棄升級 — 極光推送/個推 MAP DROP 雙軌防護。
- V45.27 (2026-04-09): 阿里雲 SLS 遙測盲區封堵 + Google Play Store 遙測路徑攔截。
- V45.26 (2026-04-08): 台灣地區深度擴充 — LINE Tag / Treasure Data / Pixnet / 台灣廣告聯播網替代域名。
- V45.25 (2026-04-07): 主流分析平台 CDN 逃逸域名封堵 (Amplitude/Mixpanel/Heap/RudderStack/Segment)。
- V45.24 (2026-04-07): 台灣特有第一方代理遙測偽裝封堵 (Dcard/Insider/GrowingIO)。
- V45.23 (2026-04-07): 跨平台第一方代理遙測封堵 (PostHog/Simple Analytics/Fathom/Pirsch)。
- V45.22 (2026-04-07): Vercel 遙測 CDN 全域封堵 + 現代圖片格式追蹤像素防護。
- V45.21 (2026-04-07): 防堵 Vercel Insights 第一方代理遙測：L1 掃描器精準突破 `script.js` 偽裝。
- V45.20 (2026-04-06): 雙軌阻擋策略：封堵微軟 App Insights (`ai.0.js`) 與 Sift Science (`siftscience.com`)。
- V45.19 (2026-04-06): 防堵 91APP 電商平台專有遙測盲區 (`deferrer-log`) 實施 204 拋棄。
- V45.18 (2026-03-31): 封堵 Alexa Metrics CDN 寄生盲區；升級 iHerb Optimizely 至 MAP DROP。
"""

import hashlib
import json
import os
import sys
import tempfile
import textwrap
import re
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

VERSION = "45.33"
RELEASE_DATE = "2026-04-09"

CURRENT_RELEASE_NOTES = """
- [Compat] Grok App 登入修復：`xai.chronosphere.io` 加入 HARD_WHITELIST.EXACT，避免 OpenTelemetry 遙測端點被 CRITICAL_PATH (`/v1/collect`) 與 PATH_BLOCK (`collect`) 規則誤殺，導致 iOS Grok App 無法登入。
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
            "/apis/": ["device_id"],  
            "/v2/api/": ["device_id"],
            "/2.0/": ["device_id"],
            "!/2.0/ad/": ["device_id"]
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
        'adsv.omgrmn.tw', 'browser.sentry-cdn.com', 'caid.china-caa.org',
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
        'jslog.coupang.com', 'mercury.coupang.com', 'pixel.dcard.tw', 'giocdn.com',
        'ad.gamer.com.tw', 'ad-geek.net', 'ad-hub.net', 'ad-serv.teepr.com', 'ad-tracking.dcard.tw',
        'analysis.tw', 'appier.net', 'b.bridgewell.com', 'cacafly.com', 'clickforce.com.tw',
        'fast-trk.com', 'funp.com', 'guoshipartners.com', 'imedia.com.tw', 'is-tracking.com',
        'itad.linetv.tw', 'likr.tw', 'scupio.com', 'sitetag.us',
        'tagtoo.co', 'tenmax.io', 'trk.tw', 'urad.com.tw', 'vpon.com',
        'adnext-a.akamaihd.net', 'toots-a.akamaihd.net',
        'analytics.twitter.com',
        'edge-analytics.amazonaws.com', 'edge-tracking.cloudflare.com',
        'insight.linkedin.com', 'px.ads.linkedin.com',
        'cdn.amplitude.com', 'cdn.eu.amplitude.com',
        'cdn.mxpnl.com', 'decide.mixpanel.com',
        'heapanalytics.com', 'heap-api.com',
        'cdn.rudderlabs.com', 'segmentapis.com',
        'tr.line.me', 'onevision.com.tw', 'pixanalytics.com', 'pixplug.in'
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
    "REDIRECT_EXTRACT_HOSTS": [
        'go.skimresources.com'
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
            'firebasedynamiclinks.googleapis.com', 'obs-tw.line-apps.com', 'obs.line-scdn.net',
            'xai.chronosphere.io'
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
        'api.pendo.io', 'c.clarity.ms', 'c.segment.com',
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
        'talkingdata.com', 'mdap.alipay.com', 'loggw-ex.alipay.com',
        'pgdt.gtimg.cn', 'afd.baidu.com', 'als.baidu.com', 'cpro.baidu.com', 'dlswbr.baidu.com',
        'duclick.baidu.com', 'feed.baidu.com', 'h2tcbox.baidu.com', 'hm.baidu.com', 'hmma.baidu.com',
        'mobads-logs.baidu.com', 'mobads.baidu.com', 'nadvideo2.baidu.com', 'nsclick.baidu.com', 'sp1.baidu.com',
        'voice.baidu.com', '3gimg.qq.com', 'fusion.qq.com', 'ios.bugly.qq.com', 'lives.l.qq.com',
        'monitor.uu.qq.com', 'pingma.qq.com', 'sdk.e.qq.com', 'wup.imtt.qq.com', 'appcloud.zhihu.com',
        'appcloud2.in.zhihu.com', 'crash2.zhihu.com', 'mqtt.zhihu.com', 'sugar.zhihu.com', 'agn.aty.sohu.com',
        'apm.gotokeep.com', 'cn-huabei-1-lg.xf-yun.com', 'log.b612kaji.com', 'pc-mon.snssdk.com',
        'sensorsdata.cn', 'stat.m.jd.com', 'trackapp.guahao.cn', 'traffic.mogujie.com', 'wmlog.meituan.com',
        'zgsdk.zhugeio.com', 'admaster.com.cn', 'adview.cn', 'alimama.com',
        'gridsum.com', 'growingio.com', 'kuaishou.com', 'miaozhen.com', 'mmstat.com',
        'pangolin-sdk-toutiao.com', 'talkingdata.cn', 'tanx.com', 'umeng.cn', 'umeng.co', 'umengcloud.com',
        'youmi.net', 'zhugeio.com', 'appnext.hs.llnwd.net', 'fusioncdn.com',
        'abema-adx.ameba.jp', 'ad.12306.cn', 'ad.360in.com', 'adroll.com', 'ads.yahoo.com',
        'adserver.yahoo.com', 'appnexus.com', 'bluekai.com', 'casalemedia.com', 'doubleclick.net',
        'googleadservices.com', 'googlesyndication.com', 'outbrain.com', 'taboola.com', 'rubiconproject.com',
        'pubmatic.com', 'openx.com', 'smartadserver.com', 'spotx.tv', 'yandex.ru', 'addthis.com',
        'onesignal.com', 'sharethis.com', 'bat.bing.com', 'clarity.ms',
        'elads.kocpc.com.tw', 'eservice.emarsys.net', 'at-display-as.deliveryhero.io',
        'stun.services.mozilla1.com',
        'analysis.chatglm.cn'
    ],
    "BLOCK_DOMAINS_WILDCARDS": [
        'sentry.io', 'pidetupop.com', 'cdn-net.com', 'lr-ingest.io',
        'aotter.net', 'ssp.yahoo.com', 'pbs.yahoo.com', 'ay.delivery',
        'cootlogix.com', 'ottadvisors.com', 'newaddiscover.com', 'app-ads-services.com',
        'app-measurement.com', 'adjust.com', 'adjust.net', 'appsflyer.com', 'onelink.me',
        'branch.io', 'app.link', 'kochava.com', 'scorecardresearch.com', 'rayjump.com',
        'mintegral.net', 'tiktokv.com', 'byteoversea.com', 'criteo.com', 'criteo.net',
        'adservices.google.com', 'ad2n.com', 'vpon.com', 'tenmax.io', 'clickforce.com.tw', 
        'onead.com.tw', 'bridgewell.com', 'tagtoo.co', 'scupio.com', 'adbottw.net',
        'useinsider.com', 'insiderone.com',
        'treasuredata.com', 'treasure-data.com',
        'tagtoo.com.tw', 'scupio.net', 'clickforce.net',
        'log.aliyuncs.com', 'sls.aliyuncs.com',
        'jpush.cn', 'jpush.io', 'jiguang.cn', 'igexin.com', 'getui.com', 'getui.net', 'gepush.com'
    ],
    "BLOCK_DOMAINS_REGEX": [
        r'^ads?\d*\.(?:ettoday\.net|ltn\.com\.tw)$',
        r'^browser-intake-[\w.-]*datadoghq\.(?:com|eu|us)$',
        r'(?:^|\.)adunblock\d*.*\.workers\.dev$'
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
        '/api/track', '/tr/', '/api/v1/event', '/rest/n/log', '/action-log',
        '/ramen/v1/events', '/_events', '/report/v1/log', '/app/mobilelog', '/api/web/ad/', 
        '/cdn/fingerprint/', '/api/device-id', '/api/visitor-id', '/ads/ga-audiences', '/doubleclick/', 
        '/google-analytics/', '/googleadservices/', '/googlesyndication/', '/googletagmanager/', 
        '/tiktok/track/', '/__utm.gif', '/j/collect', '/r/collect', '/api/batch', '/api/events', 
        '/api/v2/event', '/api/v2/events', '/collect?',
        '/data/collect', '/events/track', '/ingest/', '/ingest/otel', '/intake', '/p.gif', '/rec/bundle', '/t.gif', 
        '/track/', '/v1/pixel', '/v3/track', '/2/client/addlog_batch',
        '/plugins/easy-social-share-buttons/', '/event_report', '/log/aplus', '/v.gif', '/ad-sw.js', 
        '/ads-sw.js', '/ad-call', '/adx/', '/adsales/', '/adserver/', '/adsync/', '/adtech/', 
        '/abtesting/', '/b/ss', '/feature-flag/', '/i/adsct', '/track/m', '/track/pc', '/user-profile/', 
        'cacafly/track', '/api/v1/t', '/sa.gif', '/api/v2/rum', '/batch_resolve',
        '/acookie/', '/cookie-sync/',
        '/pixel.webp', '/beacon.webp', '/track.webp', '/0.webp', '/1.webp',
        '/pixel.svg', '/beacon.svg', '/track.svg',
        '/pixel.avif', '/beacon.avif',
        '/pixel.ico', '/beacon.ico'
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
        '/plugins/advanced-ads', '/plugins/adrotate',
        'gad_script.', '/atrk.', '/ai.0.', '/_vercel/insights/', '/_vercel/speed-insights/'
    ],
    "CRITICAL_PATH_SCRIPT_REGEX_RAW": [
        r"\/wp-content\/plugins\/[^\/]+\/.*(?:ads|ad-inserter|advanced-ads|ipa|quads)\.js(?:\?|$)",
        r"\/pagead\/js\/adsbygoogle\.js(?:\?|$)",
        r"\/ads\.js(?:\?|$)",
        r"\/adrotate\.js(?:\?|$)"
    ],
    "CRITICAL_PATH_MAP": {
        'statsig.anthropic.com': ['DROP:/v1/rgstr'],
        'logx.optimizely.com': ['DROP:/v1/events'],
        'cpdl-deferrer.91app.com': ['DROP:deferrer-log'],
        'siftscience.com': ['DROP:/v3/accounts/', 'DROP:/mobile_events'],
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
        'play.google.com': ['/log'],
        'js.stripe.com': ['/fingerprinted/'],
        'chatgpt.com': ['/ces/statsc/flush', '/v1/rgstr'],
        'tw.fd-api.com': ['DROP:/api/v5/action-log'],
        'chatbot.shopee.tw': ['/report/v1/log'],
        'data-rep.livetech.shopee.tw': ['/dataapi/dataweb/event/'],
        'shopee.tw': ['/dataapi/dataweb/event/', '/abtest/traffic/'],
        'api.tongyi.com': ['/qianwen/event/track'],
        'gw.alipayobjects.com': ['/config/loggw/'],
        'slack.com': ['/api/profiling.logging.enablement', '/api/telemetry', 'DROP:/clog/track/', 'DROP:/api/eventlog.history'],
        'slackb.com': ['DROP:/'],
        'discord.com': ['DROP:/api/v10/science', 'DROP:/api/v9/science'],
        'browser.events.data.microsoft.com': ['DROP:/'],
        'mobile.events.data.microsoft.com': ['DROP:/'],
        'self.events.data.microsoft.com': ['DROP:/'],
        'watson.telemetry.microsoft.com': ['DROP:/'],
        'jpush.cn': ['DROP:/'],
        'jpush.io': ['DROP:/'],
        'jiguang.cn': ['DROP:/'],
        'igexin.com': ['DROP:/'],
        'getui.com': ['DROP:/'],
        'getui.net': ['DROP:/'],
        'gepush.com': ['DROP:/'],
        'analysis.chatglm.cn': ['DROP:/'],
        'mp.weixin.qq.com': ['DROP:/mp/appmsgreport', 'DROP:/mp/jsmonitor', 'DROP:/mp/wapcommrepor'],
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
        'api2.amplitude.com': ['/2/httpapi', '/batch'],
        'api.eu.amplitude.com': ['/2/httpapi'],
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
        'va.vercel-scripts.com': ['/v1/script.js', '/v1/script.debug.js', '/v1/speed-insights/script.js', '/v1/speed-insights/script.debug.js'],
        'cdn.vercel-insights.com': ['/v1/script.js', '/v1/script.debug.js'],
        'vitals.vercel-analytics.com': ['/v1/vitals'],
        'us.i.posthog.com': ['/batch', '/decide', '/i/v0/e', '/capture'],
        'eu.i.posthog.com': ['/batch', '/decide', '/i/v0/e', '/capture'],
        'us-assets.i.posthog.com': ['/static/array.js'],
        'eu-assets.i.posthog.com': ['/static/array.js'],
        'scripts.simpleanalyticscdn.com': ['/latest.js', '/proxy.js', '/auto-events.js'],
        'queue.simpleanalyticscdn.com': ['/noscript.gif', '/events'],
        'simpleanalyticsexternal.com': ['/proxy.js'],
        'cdn.usefathom.com': ['/script.js'],
        'api.pirsch.io': ['/pa.js', '/api/v1/hit'],
        'assets.dcard.tw': ['/scripts/web-ad-tracking-sdk/'],
        'assets.giocdn.com': ['/2.1/gio.js', '/cdp/1.0/gio.js'],
        'd.line-scdn.net': ['/n/line_tag/'],
        'cdn.treasuredata.com': ['/sdk/'],
        'in.treasuredata.com': ['/js/v3/event/'],
        's.pixanalytics.com': ['/c.js'],
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
        'vk.com': ['/rtrg'],
        'instagram.com': ['/logging_client_events'],
        'mall.shopee.tw': ['/userstats_record/batchrecord'],
        'patronus.idata.shopeemobile.com': ['/log-receiver/api/v1/0/tw/event/batch', '/event-receiver/api/v4/tw'],
        'dp.tracking.shopee.tw': ['/v4/event_batch'],
        'live-apm.shopee.tw': ['/apmapi/v1/event'],
        'cmapi.tw.coupang.com': ['/featureflag/batchtracking', '/sdp-atf-ads/', '/sdp-btf-ads/', '/home-banner-ads/', '/category-banner-ads/', '/plp-ads/'],
        'disqus.com': ['/api/3.0/users/events', '/j/', '/tracking_pixel/'],
        'yahooapis.jp': ['/v2/acookie/lookup', '/acookie/']
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
        'data-collection', 'data-sync', 'fingerprint', 'session-replay', 'third-party-cookie',
        'user-analytics', 'user-behavior', 'user-cohort', 'user-segment', 'comscore', 'fbevents',
        'fbq', 'google-analytics', 'osano', 'sailthru', 'utag.js', '/apmapi/',
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
        "storm.mg": ["/_nuxt/track"],
        "shopee.tw": ["/api/v4/search/search_items", "/api/v4/pdp/get"],
        "uber.com": ["/go/_events"],
        "cmapi.tw.coupang.com": ["/vendor-items/"],
        "coupangcdn.com": ["/image/ccm/banner/", "/image/cmg/oms/banner/"],
        "www.google.com": ["/url", "/search", "/s2/favicons"],
        "play.googleapis.com": ["/log/batch"],
        "threads.com": ["/post/"],
        "threads.net": ["/post/"]
    }
}

# 規則資料庫統計摘要（自動計算，供跨版本比對規則數量增減）
RULES_STATS = {
    "block_domains":    len(RULES_DB["BLOCK_DOMAINS"]) + len(RULES_DB["BLOCK_DOMAINS_WILDCARDS"]) + len(RULES_DB["BLOCK_DOMAINS_REGEX"]),
    "critical_paths":   len(RULES_DB["CRITICAL_PATH_GENERIC"]) + sum(len(v) for v in RULES_DB["CRITICAL_PATH_MAP"].values()),
    "path_keywords":    len(RULES_DB["PATH_BLOCK"]) + len(RULES_DB["HIGH_CONFIDENCE"]),
    "drop_keywords":    len(RULES_DB["DROP"]) + len(RULES_DB["PRIORITY_DROP"]),
    "param_rules":      len(RULES_DB["PARAMS_GLOBAL"]) + len(RULES_DB["PARAMS_PREFIXES"]),
    "whitelist":        len(RULES_DB["SOFT_WHITELIST"]["EXACT"]) + len(RULES_DB["SOFT_WHITELIST"]["WILDCARDS"])
                        + len(RULES_DB["HARD_WHITELIST"]["EXACT"]) + len(RULES_DB["HARD_WHITELIST"]["WILDCARDS"]),
}
TOTAL_RULE_COUNT = sum(RULES_STATS.values())

# ==========================================
#  2. JS COMPILER & FORMATTER (SHARED)
# ==========================================

def _js_str_escape(s: str) -> str:
    """Escape backslashes and single quotes for safe embedding in JS single-quoted string literals."""
    return s.replace('\\', '\\\\').replace("'", "\\'")

def format_js_array(lst: List[str], indent: int = 4, items_per_line: int = 6) -> str:
    if not lst: return "[]"
    chunks = [lst[i:i + items_per_line] for i in range(0, len(lst), items_per_line)]
    lines = [(" " * indent) + ", ".join(f"'{_js_str_escape(x)}'" for x in chunk) for chunk in chunks]
    return "[\n" + ",\n".join(lines) + "\n" + (" " * (indent - 2)) + "]"

def format_js_set(lst: List[str], indent: int = 4, items_per_line: int = 6) -> str:
    if not lst: return "new Set([])"
    return f"new Set({format_js_array(lst, indent, items_per_line)})"

def format_js_map(dct: Dict[str, List[str]], indent: int = 4) -> str:
    if not dct: return "new Map([])"
    entries = []
    for k, v in dct.items():
        val_str = format_js_set(v, indent + 4, items_per_line=4)
        entries.append(f"{' ' * indent}['{_js_str_escape(k)}', {val_str}]")
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
            path_entries.append(f"{' ' * (indent + 4)}['{_js_str_escape(path)}', {param_set_str}]")
        joined_paths = ",\n".join(path_entries)
        path_map_str = f"new Map([\n{joined_paths}\n{' ' * (indent + 4)}])"
        domain_entries.append(f"{' ' * indent}['{_js_str_escape(domain)}', {path_map_str}]")
    joined_domains = ",\n".join(domain_entries)
    return f"new Map([\n{joined_domains}\n{' ' * (indent - 2)}])"

def _escape_regex(s: str) -> str:
    import re as _re
    return _re.sub(r'([.*+?^${}()|[\]\\/])', r'\\\1', s)

def _compile_keywords_to_regex(keywords: List[str], raw_regexes: List[str] = None) -> str:
    escaped = [_escape_regex(k) for k in keywords] if keywords else []
    raw = raw_regexes if raw_regexes else []
    combined = escaped + raw
    if not combined:
        return "/(?!x)x/i"
    return f"/({('|'.join(combined))})/i"

def get_js_rules_definition(platform_desc: str) -> str:
    regex_joined = ', '.join([f"/{r}/i" for r in RULES_DB['BLOCK_DOMAINS_REGEX']])
    critical_keywords = RULES_DB['CRITICAL_PATH_GENERIC'] + RULES_DB['CRITICAL_PATH_SCRIPT_ROOTS']
    critical_raw = RULES_DB.get('CRITICAL_PATH_SCRIPT_REGEX_RAW', [])
    critical_path_regex = _compile_keywords_to_regex(critical_keywords, critical_raw)
    
    return f"""/**
 * @file    URL-Ultimate-Filter-{platform_desc}.js
 * @version {VERSION}
 * @date    {RELEASE_DATE}
 * @rules   {TOTAL_RULE_COUNT} total ({RULES_STATS['block_domains']} domains, {RULES_STATS['critical_paths']} critical paths, {RULES_STATS['path_keywords']} path keywords, {RULES_STATS['param_rules']} param rules)
 * @build   SSOT Compiler — Dual-Target Compilation
 */

const CONFIG = {{ DEBUG_MODE: false, AC_SCAN_MAX_LENGTH: 600 }};
const SCRIPT_VERSION = '{VERSION}';
const SCRIPT_BUILD = 'V{VERSION} ({RELEASE_DATE}) | {TOTAL_RULE_COUNT} rules | __SSOT_TEST_COUNT__ tests';
const EMPTY_SET = new Set();

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
  REDIRECT_EXTRACT_HOSTS: {format_js_set(RULES_DB['REDIRECT_EXTRACT_HOSTS'])},

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

const PRECOMPILED_SCANNERS = {{
  HIGH_CONFIDENCE: {_compile_keywords_to_regex(RULES_DB['HIGH_CONFIDENCE'])},
  PATH_BLOCK: {_compile_keywords_to_regex(RULES_DB['PATH_BLOCK'])},
  CRITICAL_PATH: {critical_path_regex}
}};
"""

def get_js_engine_logic() -> str:
    return r"""
class CompiledScanner {
  constructor(regex) { this.regex = regex; }
  matches(text) {
    if (!text) return false;
    const target = text.length > CONFIG.AC_SCAN_MAX_LENGTH ? text.substring(0, CONFIG.AC_SCAN_MAX_LENGTH) : text;
    return this.regex.test(target);
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
    if (this.cache.has(key)) {
      this.cache.delete(key);
    } else if (this.cache.size >= this.limit) {
      const now = Date.now();
      let evicted = false;
      for (const [k, v] of this.cache) {
        if (now > v.expiry) { this.cache.delete(k); evicted = true; break; }
      }
      if (!evicted) this.cache.delete(this.cache.keys().next().value);
    }
    this.cache.set(key, { value, expiry: Date.now() + ttl });
  }
}

const highConfidenceScanner = new CompiledScanner(PRECOMPILED_SCANNERS.HIGH_CONFIDENCE);
const pathScanner = new CompiledScanner(PRECOMPILED_SCANNERS.PATH_BLOCK);
const criticalPathScanner = new CompiledScanner(PRECOMPILED_SCANNERS.CRITICAL_PATH);
const COMBINED_PATH_REGEX = [...RULES.REGEX.PATH_BLOCK, ...RULES.REGEX.HEURISTIC];
const COMBINED_PATH_SCANNER = new RegExp(COMBINED_PATH_REGEX.map(r => r.source).join('|'), 'i');
const OAUTH_PATHS_REGEX = OAUTH_SAFE_HARBOR.PATHS_REGEX;
const API_SIGNATURE_BYPASS_REGEX = RULES.REGEX.API_SIGNATURE_BYPASS;
const BLOCK_DOMAINS_REGEX = RULES.BLOCK_DOMAINS_REGEX;

const STATIC_EXTENSIONS = new Set();
const STATIC_FILENAMES = new Set();
for (const s of RULES.EXCEPTIONS.SUFFIXES) {
  if (!s) continue;
  if (s.startsWith('.')) STATIC_EXTENSIONS.add(s);
  else STATIC_FILENAMES.add(s);
}

const stats = { blocks: 0, allows: 0, toString: () => `Blocked: ${stats.blocks}, Allowed: ${stats.allows}` };
const criticalMapCache = new HighPerformanceLRUCache(256);
const hostProfileCache = new HighPerformanceLRUCache(256);

function matchesAnyRegex(regexList, text) {
  for (let i = 0; i < regexList.length; i++) {
    if (regexList[i].test(text)) return true;
  }
  return false;
}

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

function resolvePathExemptions(hostname) {
  let matches = null;
  for (const [domainOrPrefix, exemptedPaths] of RULES.EXCEPTIONS.PATH_EXEMPTIONS) {
    let isMatch = false;
    if (domainOrPrefix.endsWith('.') && /^\d/.test(domainOrPrefix)) {
      isMatch = hostname.startsWith(domainOrPrefix);
    } else {
      isMatch = (hostname === domainOrPrefix || hostname.endsWith('.' + domainOrPrefix));
    }
    if (isMatch) {
      if (!matches) matches = [];
      matches.push(exemptedPaths);
    }
  }
  return matches;
}

function resolveScopedParamExemptions(hostname) {
  let domainExemptions = RULES.PARAMS.SCOPED_EXEMPTIONS.get(hostname);
  if (domainExemptions) return domainExemptions;
  for (const [domain, paths] of RULES.PARAMS.SCOPED_EXEMPTIONS) {
    if (hostname.endsWith('.' + domain)) return paths;
  }
  return null;
}

function getHostProfile(hostname) {
  const cached = hostProfileCache.get(hostname);
  if (cached !== null) return cached;

  const profile = {
    isOAuthSafeHarbor: OAUTH_SAFE_HARBOR.DOMAINS.has(hostname) && hostname !== 'accounts.youtube.com',
    isParamCleaningExempted: isDomainMatch(PARAM_CLEANING_EXEMPTED_DOMAINS.EXACT, PARAM_CLEANING_EXEMPTED_DOMAINS.WILDCARDS, hostname),
    isSilentRewriteDomain: isDomainMatch(SILENT_REWRITE_DOMAINS.EXACT, SILENT_REWRITE_DOMAINS.WILDCARDS, hostname),
    isAbsoluteBypass: isDomainMatch(ABSOLUTE_BYPASS_DOMAINS.EXACT, ABSOLUTE_BYPASS_DOMAINS.WILDCARDS, hostname),
    isPriorityBlocked: isDomainMatch(EMPTY_SET, RULES.PRIORITY_BLOCK_DOMAINS, hostname),
    isRedirector: RULES.REDIRECTOR_HOSTS.has(hostname),
    isRedirectExtract: RULES.REDIRECT_EXTRACT_HOSTS.has(hostname),
    isSoftWhitelisted: isDomainMatch(RULES.SOFT_WHITELIST.EXACT, RULES.SOFT_WHITELIST.WILDCARDS, hostname),
    isHardWhitelisted: isDomainMatch(RULES.HARD_WHITELIST.EXACT, RULES.HARD_WHITELIST.WILDCARDS, hostname),
    isBlockedDomain: isDomainMatch(RULES.BLOCK_DOMAINS, RULES.BLOCK_DOMAINS_WILDCARDS, hostname) || matchesAnyRegex(BLOCK_DOMAINS_REGEX, hostname),
    pathExemptions: resolvePathExemptions(hostname),
    scopedParamExemptions: resolveScopedParamExemptions(hostname)
  };

  hostProfileCache.set(hostname, profile, 300000);
  return profile;
}

const HELPERS = {
  isStaticFile: (pathLowerMaybeWithQuery) => {
    if (!pathLowerMaybeWithQuery) return false;
    const queryIndex = pathLowerMaybeWithQuery.indexOf('?');
    const cleanPath = queryIndex >= 0 ? pathLowerMaybeWithQuery.substring(0, queryIndex) : pathLowerMaybeWithQuery;
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

  isPathExemptedForDomain: (matchedExemptions, pathLower) => {
    if (!matchedExemptions) return false;
    for (let i = 0; i < matchedExemptions.length; i++) {
      for (const exemptedPath of matchedExemptions[i]) {
        if (pathLower.includes(exemptedPath)) return true;
      }
    }
    return false;
  },

  isScopedParamAllowed: (domainExemptions, pathLower, lowerKey) => {
    if (!domainExemptions) return false;

    for (const [pathStr, allowedParamsSet] of domainExemptions) {
      if (pathStr.startsWith('!')) {
        const actualPath = pathStr.substring(1);
        if (pathLower.includes(actualPath) && allowedParamsSet.has(lowerKey)) {
          return false;
        }
      }
    }

    for (const [pathStr, allowedParamsSet] of domainExemptions) {
      if (!pathStr.startsWith('!')) {
        if (pathLower.includes(pathStr) && allowedParamsSet.has(lowerKey)) {
          return true;
        }
      }
    }

    return false;
  },

  cleanTrackingParams: (urlStr, hostname, pathLower, hostProfile) => {
    if (!urlStr.includes('?')) return null;
    if (/[?&](signature|sig|hmac)=/i.test(pathLower)) return null;
    if (hostProfile.isOAuthSafeHarbor) return null;
    if (matchesAnyRegex(OAUTH_PATHS_REGEX, pathLower)) return null;
    if (hostProfile.isParamCleaningExempted) return null;

    let rewriteType = '302';
    if (matchesAnyRegex(API_SIGNATURE_BYPASS_REGEX, pathLower) ||
        hostname.startsWith('api.') || hostname.startsWith('appapi.') ||
        hostProfile.isSilentRewriteDomain) {
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
      if (qs.indexOf(';') >= 0) qs = qs.replace(/;/g, '&');

      const pairs = qs.split('&');
      const kept = [];
      const scopedParamExemptions = hostProfile.scopedParamExemptions;
      let changed = false;

      for (let i = 0; i < pairs.length; i++) {
        const pair = pairs[i];
        if (!pair) { kept.push(pair); continue; }
        const eqIdx = pair.indexOf('=');
        const key = eqIdx >= 0 ? pair.substring(0, eqIdx) : pair;
        const lowerKey = key.toLowerCase();

        if (RULES.PARAMS.WHITELIST.has(lowerKey) || HELPERS.isScopedParamAllowed(scopedParamExemptions, pathLower, lowerKey)) {
          kept.push(pair); continue;
        }

        if (RULES.PARAMS.GLOBAL.has(lowerKey) || RULES.PARAMS.COSMETIC.has(lowerKey)) { changed = true; continue; }

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

        if (matchesAnyRegex(RULES.PARAMS.GLOBAL_REGEX, lowerKey) || matchesAnyRegex(RULES.PARAMS.PREFIXES_REGEX, lowerKey)) {
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

function _performCleaning(url, hostname, pathLower, hostProfile) {
  const cleanResult = HELPERS.cleanTrackingParams(url, hostname, pathLower, hostProfile);
  if (cleanResult) {
    stats.allows++;
    if (cleanResult.type === 'REWRITE') return { url: cleanResult.url };
    return { response: { status: 302, headers: { Location: cleanResult.url } } };
  }
  return null;
}

function processRequest(request) {
  const url = request && request.url;
  if (!url) return null;

  try {
    const _pe = url.indexOf('://');
    const _hs = _pe >= 0 ? _pe + 3 : 0;
    const _ps = url.indexOf('/', _hs);
    const _hp = _ps >= 0 ? url.substring(_hs, _ps) : url.substring(_hs);
    const _port = _hp.indexOf(':');
    const hostname = (_port >= 0 ? _hp.substring(0, _port) : _hp).toLowerCase();
    const hostProfile = getHostProfile(hostname);

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

    if (hostProfile.isPriorityBlocked) {
      const _earlyMap = getCriticalBlockedPaths(hostname);
      if (_earlyMap) {
        for (const bp of _earlyMap) {
          if (bp && bp.startsWith('DROP:') && pathLower.includes(bp.substring(5))) {
            stats.blocks++;
            return { response: { status: 204 } };
          }
        }
      }
      stats.blocks++;
      return { response: { status: 403, body: 'Blocked by P0' } };
    }

    if (hostProfile.isRedirectExtract) {
      let extractedUrl = null;
      const rawPath = url.substring(url.indexOf('/', url.indexOf('://') + 3) + 1);
      if (rawPath) {
        try {
          const decoded = decodeURIComponent(rawPath);
          if (decoded.startsWith('http://') || decoded.startsWith('https://')) extractedUrl = decoded;
        } catch (_) {}
      }
      if (!extractedUrl && url.includes('?')) {
        const qs = url.substring(url.indexOf('?') + 1);
        const pairs = qs.split('&');
        for (let i = 0; i < pairs.length; i++) {
          const pair = pairs[i];
          if (pair.startsWith('url=')) {
            try {
              const val = decodeURIComponent(pair.substring(4));
              if (val.startsWith('http://') || val.startsWith('https://')) { extractedUrl = val; break; }
            } catch (_) {}
          }
        }
      }
      if (extractedUrl) {
        stats.allows++;
        return { response: { status: 302, headers: { Location: extractedUrl } } };
      }
      stats.blocks++;
      return { response: { status: 403, body: 'Blocked Redirector Asset' } };
    }

    if (hostProfile.isRedirector) {
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
            if (isDrop) return { response: { status: 204 } };
            return { response: { status: 403, body: 'Blocked by Map' } };
          }
        }
      }
    }

    const isSoftWhitelisted = hostProfile.isSoftWhitelisted;
    if (!isSoftWhitelisted && hostProfile.isBlockedDomain) {
      stats.blocks++;
      return { response: { status: 403, body: 'Blocked by Domain' } };
    }

    if (hostProfile.isOAuthSafeHarbor) {
      stats.allows++;
      return null;
    }

    if (hostProfile.isAbsoluteBypass) {
      stats.allows++;
      return null;
    }

    if (hostProfile.isHardWhitelisted) {
      stats.allows++;
      return _performCleaning(url, hostname, pathLower, hostProfile);
    }

    if (HELPERS.isPathExemptedForDomain(hostProfile.pathExemptions, pathLower)) {
      stats.allows++;
      return _performCleaning(url, hostname, pathLower, hostProfile);
    }

    const isExplicitlyAllowed = HELPERS.isPathExplicitlyAllowed(pathLower);
    const isStatic = HELPERS.isStaticFile(pathLower);

    if (!isExplicitlyAllowed && !isStatic) {
      for (const k of RULES.KEYWORDS.PRIORITY_DROP) {
        if (pathLower.includes(k)) {
          stats.blocks++;
          return { response: { status: 204 } };
        }
      }
    }

    if (!isExplicitlyAllowed && highConfidenceScanner.matches(pathLower)) {
      stats.blocks++;
      return { response: { status: 403, body: 'Blocked by High Confidence Keyword' } };
    }

    if (criticalPathScanner.matches(pathLower)) {
      stats.blocks++;
      return { response: { status: 403, body: 'Blocked by L1 (Script/Path)' } };
    }

    if (hostname === 'cmapi.tw.coupang.com' && /\/.*-ads\//.test(pathLower)) {
      stats.blocks++;
      return { response: { status: 403, body: 'Blocked by Coupang Omni-Block' } };
    }

    if (!(isSoftWhitelisted && isStatic) && !isExplicitlyAllowed && !isStatic) {
      if (pathScanner.matches(pathLower)) {
        stats.blocks++;
        return { response: { status: 403, body: 'Blocked by Keyword' } };
      }
      if (COMBINED_PATH_SCANNER.test(pathLower)) {
        stats.blocks++;
        return { response: { status: 403, body: 'Blocked by Regex' } };
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

    return _performCleaning(url, hostname, pathLower, hostProfile);

  } catch (err) {
    if (CONFIG.DEBUG_MODE) console.log(`[Error] ${err}`);
  }
  stats.allows++;
  return null;
}

const BENCHMARK_CASES = [
  { label: 'P0 Block', url: 'https://ads.google.com/pagead/adview?utm_source=test&id=1' },
  { label: 'Map Drop', url: 'https://slackb.com/traces/v1/list_of_spans/json' },
  { label: 'Silent Rewrite', url: 'https://guide.104.com.tw/career/compare/major/?utm_source=104&utm_medium=whitebar' },
  { label: 'Static Allow', url: 'https://static.104.com.tw/104main/jb/area/manjb/home/json/jobNotify/ad.json?v=1772752285970' },
  { label: 'Critical Path', url: 'https://www.youtube.com/api/stats/qoe?event=1&cpn=2' },
  { label: 'Soft WL Clean', url: 'https://chatgpt.com/backend-api/conversation?utm_source=test&model=gpt-5' },
  { label: 'Path Exempt', url: 'https://foo.shopee.tw/api/v4/pdp/get?adsid=1&device_id=2' },
  { label: 'Coupang Block', url: 'https://cmapi.tw.coupang.com/api/v1/test-ads/item?x=1' },
  { label: 'Param Exempt', url: 'https://subdomain.feedly.com/v3/streams/contents?token=1&utm_source=dropme' },
  { label: 'Static Prefix', url: 'https://example.com/assets/app.js?fbclid=123&utm_source=abc' }
];
const BENCHMARK_STORE_PREFIX = 'url-ultimate-filter.benchmark.';

function benchmarkNow() {
  if (typeof performance !== 'undefined' && performance && typeof performance.now === 'function') {
    return performance.now();
  }
  return Date.now();
}

function shouldRunBenchmark() {
  return typeof $argument !== 'undefined' &&
    typeof $argument === 'string' &&
    $argument.toLowerCase().indexOf('benchmark') >= 0;
}

function medianOfNumbers(values) {
  const sorted = values.slice().sort((a, b) => a - b);
  return sorted[sorted.length >> 1];
}

function getPreviousVersion(versionText) {
  const match = /^(\d+)\.(\d+)$/.exec(versionText);
  if (!match) return null;

  let major = parseInt(match[1], 10);
  let minor = parseInt(match[2], 10);
  const width = match[2].length;

  if (minor > 0) {
    minor -= 1;
  } else if (major > 0) {
    major -= 1;
    minor = Math.pow(10, width) - 1;
  } else {
    return null;
  }

  return `${major}.${String(minor).padStart(width, '0')}`;
}

function readBenchmarkRecord(versionText) {
  if (typeof $persistentStore === 'undefined' || !$persistentStore || typeof $persistentStore.read !== 'function') {
    return null;
  }

  try {
    const raw = $persistentStore.read(BENCHMARK_STORE_PREFIX + versionText);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    return parsed && parsed.version === versionText ? parsed : null;
  } catch (_) {
    return null;
  }
}

function writeBenchmarkRecord(record) {
  if (typeof $persistentStore === 'undefined' || !$persistentStore || typeof $persistentStore.write !== 'function') {
    return false;
  }

  try {
    return !!$persistentStore.write(JSON.stringify(record), BENCHMARK_STORE_PREFIX + record.version);
  } catch (_) {
    return false;
  }
}

function formatDelta(currentValue, previousValue) {
  if (typeof previousValue !== 'number') return 'baseline missing';
  const delta = currentValue - previousValue;
  const percent = previousValue !== 0 ? (delta / previousValue) * 100 : null;
  const sign = delta > 0 ? '+' : '';
  if (percent === null) return `${sign}${delta.toFixed(2)} us`;
  return `${sign}${delta.toFixed(2)} us (${sign}${percent.toFixed(1)}%)`;
}

function runBenchmarkSuite() {
  const warmupIterations = 20;
  const iterationsPerPass = 100;
  const measuredPasses = 7;
  const statsSnapshot = { blocks: stats.blocks, allows: stats.allows };
  const results = [];

  try {
    for (let caseIndex = 0; caseIndex < BENCHMARK_CASES.length; caseIndex++) {
      const benchmarkCase = BENCHMARK_CASES[caseIndex];
      const request = { url: benchmarkCase.url };

      for (let i = 0; i < warmupIterations; i++) processRequest(request);

      const samplesMs = [];
      for (let pass = 0; pass < measuredPasses; pass++) {
        const startedAt = benchmarkNow();
        for (let i = 0; i < iterationsPerPass; i++) processRequest(request);
        samplesMs.push(benchmarkNow() - startedAt);
      }

      const medianMs = medianOfNumbers(samplesMs);
      results.push({
        label: benchmarkCase.label,
        medianUsPerRequest: (medianMs * 1000) / iterationsPerPass
      });
    }
  } finally {
    stats.blocks = statsSnapshot.blocks;
    stats.allows = statsSnapshot.allows;
  }

  const overallMedian = medianOfNumbers(results.map(r => r.medianUsPerRequest));
  const currentRecord = {
    version: SCRIPT_VERSION,
    overallMedianUs: overallMedian,
    cases: results.reduce((acc, item) => {
      acc[item.label] = item.medianUsPerRequest;
      return acc;
    }, {}),
    timestamp: Date.now()
  };
  const previousVersion = getPreviousVersion(SCRIPT_VERSION);
  const previousRecord = previousVersion ? readBenchmarkRecord(previousVersion) : null;
  writeBenchmarkRecord(currentRecord);

  const contentLines = [
    `V${SCRIPT_VERSION} Surge Benchmark`,
    `Cases: ${BENCHMARK_CASES.length}, Warmup: ${warmupIterations}, Passes: ${measuredPasses}x${iterationsPerPass}`
  ];

  if (previousVersion) {
    if (previousRecord) {
      contentLines.push(`Median: ${overallMedian.toFixed(2)} us/request (vs V${previousVersion}: ${formatDelta(overallMedian, previousRecord.overallMedianUs)})`);
    } else {
      contentLines.push(`Median: ${overallMedian.toFixed(2)} us/request`);
      contentLines.push(`vs V${previousVersion}: baseline missing on this device`);
    }
  } else {
    contentLines.push(`Median: ${overallMedian.toFixed(2)} us/request`);
  }

  for (let i = 0; i < results.length; i++) {
    const current = results[i];
    if (previousRecord && typeof previousRecord.cases[current.label] === 'number') {
      contentLines.push(`${i + 1}. ${current.label}: ${current.medianUsPerRequest.toFixed(2)} us (vs V${previousVersion}: ${formatDelta(current.medianUsPerRequest, previousRecord.cases[current.label])})`);
    } else {
      contentLines.push(`${i + 1}. ${current.label}: ${current.medianUsPerRequest.toFixed(2)} us`);
    }
  }

  const content = contentLines.join('\n');
  if (typeof $notification !== 'undefined' && $notification && typeof $notification.post === 'function') {
    try { $notification.post('URL Ultimate Filter', 'Surge Benchmark Completed', content); } catch (_) {}
  }
  return { title: 'URL Ultimate Filter Benchmark', content };
}
"""

def compile_surge() -> str:
    js = get_js_rules_definition("Surge") + get_js_engine_logic()
    wrapper = """
if (typeof $request !== 'undefined') {
  $done(processRequest($request));
} else {
  if (typeof $done !== 'undefined') {
    if (shouldRunBenchmark()) $done(runBenchmarkSuite());
    else $done({ title: 'URL Ultimate Filter', content: `V${SCRIPT_VERSION} Active\\n${stats.toString()}` });
  }
}
"""
    return js + wrapper

def compile_surge_reject_list() -> str:
    """Generate Surge REJECT-DROP rule list for DNS-level blocking.

    This complements the JS script by preventing DNS/TCP connections entirely.
    The JS script handles HTTP-level interception (204/403/302) but cannot
    prevent the network connection from being established.
    """
    # Collect whitelisted domains to avoid false positives
    wl_exact = set(RULES_DB["HARD_WHITELIST"]["EXACT"]) | set(RULES_DB["SOFT_WHITELIST"]["EXACT"])
    wl_wildcards = set(RULES_DB["HARD_WHITELIST"]["WILDCARDS"]) | set(RULES_DB["SOFT_WHITELIST"]["WILDCARDS"])

    def _is_wl(domain: str) -> bool:
        if domain in wl_exact:
            return True
        parts = domain.split('.')
        for i in range(len(parts)):
            suffix = '.'.join(parts[i:])
            if suffix in wl_wildcards:
                return True
        return False

    lines = [
        f"# URL Ultimate Filter - Surge REJECT Rule Set",
        f"# Version: V{VERSION} ({RELEASE_DATE})",
        f"# Auto-generated by SSOT Compiler",
        f"#",
        f"# Usage in Surge.conf:",
        f"#   [Rule]",
        f"#   RULE-SET,URL-Ultimate-Filter-Surge-REJECT.list,REJECT-DROP",
        f"#",
        f"# Place AFTER any DOMAIN rules you want to ALLOW (first match wins).",
        f"# REJECT-DROP = silent TCP drop (no response sent, connection times out).",
        f"# This prevents DNS resolution + TCP handshake, eliminating request noise.",
        f"#",
    ]

    # --- Section 1: PRIORITY_BLOCK_DOMAINS (highest priority, suffix match) ---
    lines.append(f"# === PRIORITY BLOCK ({len(RULES_DB['PRIORITY_BLOCK_DOMAINS'])} domains) ===")
    for d in sorted(set(RULES_DB["PRIORITY_BLOCK_DOMAINS"])):
        lines.append(f"DOMAIN-SUFFIX,{d},REJECT-DROP")

    # --- Section 2: BLOCK_DOMAINS (exact match, skip whitelisted) ---
    block_exact = [d for d in RULES_DB["BLOCK_DOMAINS"] if not _is_wl(d)]
    lines.append(f"# === BLOCK DOMAINS ({len(block_exact)} exact) ===")
    for d in sorted(set(block_exact)):
        lines.append(f"DOMAIN,{d},REJECT-DROP")

    # --- Section 3: BLOCK_DOMAINS_WILDCARDS (suffix match, skip whitelisted) ---
    block_wc = [d for d in RULES_DB["BLOCK_DOMAINS_WILDCARDS"] if not _is_wl(d)]
    lines.append(f"# === BLOCK WILDCARDS ({len(block_wc)} suffix) ===")
    for d in sorted(set(block_wc)):
        lines.append(f"DOMAIN-SUFFIX,{d},REJECT-DROP")

    # --- Section 4: MAP DROP domains (full-domain DROP:/) ---
    map_drop = sorted({d for d, paths in RULES_DB["CRITICAL_PATH_MAP"].items()
                       if any(p == 'DROP:/' for p in paths) and not _is_wl(d)})
    lines.append(f"# === MAP DROP - Silent 204 Domains ({len(map_drop)} domains) ===")
    for d in map_drop:
        if not any(d == bd or d.endswith('.' + bd) for bd in
                   set(RULES_DB["BLOCK_DOMAINS"]) | set(RULES_DB["BLOCK_DOMAINS_WILDCARDS"]) | set(RULES_DB["PRIORITY_BLOCK_DOMAINS"])):
            lines.append(f"DOMAIN,{d},REJECT-DROP")

    total_rules = sum(1 for l in lines if l.startswith("DOMAIN"))
    lines.insert(12, f"# Total: {total_rules} rules")
    lines.insert(13, f"#")

    return "\n".join(lines) + "\n"


def compile_tampermonkey() -> str:
    header = f"""// ==UserScript==
// @name         URL Ultimate Filter V{VERSION}
// @namespace    http://tampermonkey.net/
// @version      {VERSION}
// @date         {RELEASE_DATE}
// @description  SSOT 前端防護盾牌 V{VERSION} ({RELEASE_DATE}) | {TOTAL_RULE_COUNT} rules — 極簡盾牌 UI，獨立計數器，點擊外部自動收合。
// @rules        {TOTAL_RULE_COUNT} total ({RULES_STATS['block_domains']} domains · {RULES_STATS['critical_paths']} critical · {RULES_STATS['param_rules']} param)
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
        dropped: new Map(),
        cleaned: new Map(),
        allowed: new Map(),
        countBlocked: 0,
        countDropped: 0,
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
        recordDrop: function(u) { 
            this.countDropped++;
            let c = 1;
            if(this.dropped.has(u)) { c = this.dropped.get(u) + 1; this.dropped.delete(u); }
            else if(this.dropped.size >= 50) this.dropped.delete(this.dropped.keys().next().value);
            this.dropped.set(u, c); 
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
        panel.style.cssText = 'display:none; position:absolute; bottom:0; right:0; width:400px; background:#0f172a; border: 1px solid #334155; border-radius:12px; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5); overflow:hidden; flex-direction:column; color:#f8fafc;';
        
        const header = document.createElement('div');
        header.style.cssText = 'display:flex; justify-content:space-between; align-items:center; padding:12px 16px; background:#1e293b; border-bottom:1px solid #334155; user-select:none;';
        header.innerHTML = `<div style="font-weight:600; display:flex; align-items:center; gap:8px; color:#6366F1;"><span style="font-size:15px;">\u{1F6E1}\uFE0F</span> URL Ultimate Filter V${SCRIPT_VERSION}</div>`;
        panel.appendChild(header);
        
        const tabsRow = document.createElement('div');
        tabsRow.style.cssText = 'display:flex; padding:8px; gap:6px; background:#0f172a; border-bottom:1px solid #334155;';
        
        const createTab = (id, label, color) => {
            const t = document.createElement('div');
            t.id = `ssot-tab-${id}`;
            t.title = `點擊展開/收合 ${label} 列表`;
            t.style.cssText = `flex:1; text-align:center; padding:8px 2px; cursor:pointer; border-radius:6px; transition:all 0.2s; border-bottom:2px solid transparent; user-select:none; background:transparent;`;
            t.innerHTML = `<div style="color:${color}; font-weight:700; font-size:16px; line-height:1.2;" id="ssot-cnt-${id}">0</div><div style="color:#94a3b8; font-size:10px; margin-top:2px; font-weight:600; text-transform:uppercase;">${label}</div>`;
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
        tabsRow.appendChild(createTab('dropped', 'Dropped', '#8b5cf6'));
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
        document.getElementById('ssot-cnt-dropped').innerText = tmStats.countDropped;
        document.getElementById('ssot-cnt-cleaned').innerText = tmStats.countCleaned;
        document.getElementById('ssot-cnt-allowed').innerText = tmStats.countAllowed;

        ['blocked', 'dropped', 'cleaned', 'allowed'].forEach(t => {
            const el = document.getElementById(`ssot-tab-${t}`);
            if (!el) return;
            if (activeTab === t) {
                el.style.backgroundColor = '#1e293b';
                const colors = { blocked:'#ef4444', dropped:'#8b5cf6', cleaned:'#10b981', allowed:'#cbd5e1' };
                el.style.borderBottom = `2px solid ${colors[t]}`;
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
            } else if (activeTab === 'dropped') {
                if (tmStats.dropped.size === 0) listHtml = `<div style="padding:16px; text-align:center; color:#64748b; font-size:12px;">無拋棄紀錄</div>`;
                else listHtml = Array.from(tmStats.dropped.entries()).reverse().map(([u, c]) => `<div style="${itemStyle} color:#c4b5fd;">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                        <span>${u}</span>
                        ${c > 1 ? `<span style="${badgeStyle} background:#4c1d95; color:#ddd6fe;">x${c}</span>` : ''}
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

    // --- Clipboard Interceptor 模組 ---
    function cleanTextUrls(text) {
        if (!text || typeof text !== 'string') return { text, modified: false };
        const urlRegex = /(https?:\/\/[a-zA-Z0-9\-._~:/?#[\]@!$&'()*+,;=%]+)/gi;
        let modified = false;
        let cleanedText = text.replace(urlRegex, (match) => {
            let url = match;
            let trailing = '';
            while (url.length > 0 && /[.,;?!。，、！？」』】]$/.test(url)) {
                trailing = url.slice(-1) + trailing;
                url = url.slice(0, -1);
            }
            try {
                const absoluteUrl = new URL(url, location.origin).href;
                const action = applyFilter(absoluteUrl);
                if (action && action.url && absoluteUrl !== action.url) {
                    tmStats.recordClean(absoluteUrl, action.url);
                    if (CONFIG.DEBUG_MODE) console.log(`[SSOT-TM] 📋 Clipboard Cleaned: ${absoluteUrl} -> ${action.url}`);
                    modified = true;
                    return action.url + trailing;
                }
            } catch(e) {}
            return match; 
        });
        return { text: cleanedText, modified: modified };
    }

    if (navigator.clipboard && navigator.clipboard.writeText) {
        const origWriteText = navigator.clipboard.writeText.bind(navigator.clipboard);
        navigator.clipboard.writeText = function(text) {
            const result = cleanTextUrls(text);
            return origWriteText(result.text);
        };
    }

    document.addEventListener('copy', (e) => {
        if (e.clipboardData && e.clipboardData.getData('text/plain')) return;
        const selection = document.getSelection();
        if (!selection || selection.isCollapsed) return;
        const selectedText = selection.toString();
        const result = cleanTextUrls(selectedText);
        if (result.modified) {
            e.preventDefault();
            e.clipboardData.setData('text/plain', result.text);
        }
    }, true);
    // --- Clipboard Interceptor 模組結束 ---

    // --- Property Setter Hook (動態腳本屬性攔截器) ---
    function hookProperty(elementClass, propertyName) {
        const origDesc = Object.getOwnPropertyDescriptor(elementClass.prototype, propertyName);
        if (origDesc && origDesc.set) {
            Object.defineProperty(elementClass.prototype, propertyName, {
                set: function(val) {
                    if (val && typeof val === 'string') {
                        try {
                            const absoluteUrl = new URL(val, location.origin).href;
                            const action = applyFilter(absoluteUrl);
                            if (action && action.response) {
                                if (action.response.status === 403) {
                                    tmStats.recordBlock(absoluteUrl);
                                    if (CONFIG.DEBUG_MODE) console.log(`[SSOT-TM] 🚫 Property Hook Blocked: ${absoluteUrl}`);
                                    return; // 物理阻斷賦值，瀏覽器完全不發送請求
                                } else if (action.response.status === 204) {
                                    tmStats.recordDrop(absoluteUrl);
                                    if (CONFIG.DEBUG_MODE) console.log(`[SSOT-TM] 👻 Property Hook Dropped: ${absoluteUrl}`);
                                    return; // 物理阻斷賦值，瀏覽器完全不發送請求
                                }
                            } else if (action && action.url && val !== action.url) {
                                tmStats.recordClean(absoluteUrl, action.url);
                                val = action.url;
                            }
                        } catch(e) {}
                    }
                    return origDesc.set.call(this, val);
                },
                get: origDesc.get
            });
        }
    }
    // 攔截三大核心注入點，解決 MutationObserver 的時間差盲區
    hookProperty(HTMLScriptElement, 'src');
    hookProperty(HTMLImageElement, 'src');
    hookProperty(HTMLIFrameElement, 'src');
    // --- Property Setter Hook 結束 ---

    let _pendingDrops = 0;
    const MAX_PENDING_DROPS = 64; 
    const origFetch = window.fetch;
    window.fetch = async function(...args) {
        let url = typeof args[0] === 'string' ? args[0] : (args[0] && args[0].url ? args[0].url : '');
        if (url) {
            try { url = new URL(url, location.origin).href; } catch(e){}
            const action = applyFilter(url);
            if (action) {
                if (action.response) {
                    if (action.response.status === 403) {
                        tmStats.recordBlock(url);
                        if (CONFIG.DEBUG_MODE) console.log(`[SSOT-TM] 🚫 Blocked: ${url}`);
                        return Promise.reject(new Error("Blocked by URL Ultimate Filter SSOT"));
                    } else if (action.response.status === 204) {
                        tmStats.recordDrop(url);
                        if (CONFIG.DEBUG_MODE) console.log(`[SSOT-TM] 👻 Dropped (Delayed Mock): ${url}`);
                        const mock204 = () => new Response(null, { status: 204, statusText: 'No Content' });
                        if (_pendingDrops >= MAX_PENDING_DROPS) return Promise.resolve(mock204());
                        const delay = Math.floor(Math.random() * 100) + 50;
                        _pendingDrops++;
                        return new Promise(resolve => {
                            setTimeout(() => {
                                _pendingDrops--;
                                resolve(mock204());
                            }, delay);
                        });
                    } else if (action.response.status === 302 && action.response.headers && action.response.headers.Location) {
                        const cleanedUrl = action.response.headers.Location;
                        tmStats.recordClean(url, cleanedUrl);
                        if (CONFIG.DEBUG_MODE) console.log(`[SSOT-TM] ✏️ Fetch Cleaned (302): ${url} -> ${cleanedUrl}`);
                        if (typeof args[0] === 'string') args[0] = cleanedUrl;
                        else args[0] = new Request(cleanedUrl, args[0]);
                    }
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
        this._ssotAction = null;
        this._ssotUrl = '';
        if (url) {
            try {
                let absoluteUrl = new URL(url, location.origin).href;
                this._ssotUrl = absoluteUrl;
                const action = applyFilter(absoluteUrl);
                if (action) {
                    if (action.response) {
                        if (action.response.status === 403) {
                            tmStats.recordBlock(absoluteUrl);
                            this._ssotAction = 403;
                        } else if (action.response.status === 204) {
                            tmStats.recordDrop(absoluteUrl);
                            this._ssotAction = 204;
                        } else if (action.response.status === 302 && action.response.headers && action.response.headers.Location) {
                            const cleanedUrl = action.response.headers.Location;
                            tmStats.recordClean(absoluteUrl, cleanedUrl);
                            url = cleanedUrl;
                        }
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
        if (this._ssotAction === 403) {
            this.dispatchEvent(new Event('error'));
            return;
        } else if (this._ssotAction === 204) {
            const mockUrl = this._ssotUrl;
            Object.defineProperties(this, {
                readyState: { get: () => 4 },
                status: { get: () => 204 },
                statusText: { get: () => 'No Content' },
                response: { get: () => '' },
                responseText: { get: () => '' },
                responseURL: { get: () => mockUrl },
                getAllResponseHeaders: { value: () => 'content-length: 0\r\n' },
                getResponseHeader: { value: (name) => null }
            });
            const fireXhrEvents = () => {
                this.dispatchEvent(new Event('readystatechange'));
                this.dispatchEvent(new Event('load'));
                this.dispatchEvent(new Event('loadend'));
            };
            if (_pendingDrops >= MAX_PENDING_DROPS) { fireXhrEvents(); return; }
            const delay = Math.floor(Math.random() * 100) + 50;
            _pendingDrops++;
            setTimeout(() => {
                _pendingDrops--;
                fireXhrEvents();
            }, delay);
            return;
        }
        return origSend.apply(this, args);
    };

    if (navigator.sendBeacon) {
        const origSendBeacon = navigator.sendBeacon.bind(navigator);
        const beaconInterceptor = function(url, data) {
            if (url) {
                try {
                    let absoluteUrl = new URL(url, location.origin).href;
                    const action = applyFilter(absoluteUrl);
                    if (action && action.response) {
                        if (action.response.status === 403) {
                            tmStats.recordBlock(absoluteUrl);
                            if (CONFIG.DEBUG_MODE) console.log(`[SSOT-TM] 🚫 Beacon Blocked: ${absoluteUrl}`);
                            return false;
                        } else if (action.response.status === 204) {
                            tmStats.recordDrop(absoluteUrl);
                            if (CONFIG.DEBUG_MODE) console.log(`[SSOT-TM] 👻 Beacon Dropped (Fake Success): ${absoluteUrl}`);
                            return true;
                        }
                    }
                } catch(e){}
            }
            return origSendBeacon(url, data);
        };

        const desc = Object.getOwnPropertyDescriptor(navigator, 'sendBeacon');
        const isLocked = desc && (desc.configurable === false || desc.writable === false);

        if (!isLocked) {
            try {
                navigator.sendBeacon = navigator.sendBeacon;
                navigator.sendBeacon = beaconInterceptor;
            } catch(e) {}
        }

        if (navigator.sendBeacon !== beaconInterceptor && typeof Proxy !== 'undefined') {
            try {
                const navProxy = new Proxy(navigator, {
                    get(target, prop, receiver) {
                        if (prop === 'sendBeacon') return beaconInterceptor;
                        const val = Reflect.get(target, prop, receiver);
                        return typeof val === 'function' ? val.bind(target) : val;
                    }
                });
                Object.defineProperty(window, 'navigator', {
                    get: () => navProxy,
                    configurable: true
                });
                if (CONFIG.DEBUG_MODE) console.log('[SSOT-TM] ⚔️ sendBeacon Anti-Tampering: Proxy Defusion Active');
            } catch(e) {
                if (CONFIG.DEBUG_MODE) console.log('[SSOT-TM] ⚠️ sendBeacon Anti-Tampering: Proxy fallback failed, beacon may leak');
            }
        }
    }
    
    function patchIframeBeacon(iframe) {
        try {
            const iframeWin = iframe.contentWindow;
            if (!iframeWin || !iframeWin.navigator || !iframeWin.navigator.sendBeacon) return;
            const iframeOrigBeacon = iframeWin.navigator.sendBeacon.bind(iframeWin.navigator);
            iframeWin.navigator.sendBeacon = function(url, data) {
                if (url) {
                    try {
                        let absoluteUrl = new URL(url, location.origin).href;
                        const action = applyFilter(absoluteUrl);
                        if (action && action.response) {
                            if (action.response.status === 403) {
                                tmStats.recordBlock(absoluteUrl);
                                if (CONFIG.DEBUG_MODE) console.log(`[SSOT-TM] 🚫 iframe Beacon Blocked: ${absoluteUrl}`);
                                return false;
                            } else if (action.response.status === 204) {
                                tmStats.recordDrop(absoluteUrl);
                                if (CONFIG.DEBUG_MODE) console.log(`[SSOT-TM] 👻 iframe Beacon Dropped: ${absoluteUrl}`);
                                return true;
                            }
                        }
                    } catch(e){}
                }
                return iframeOrigBeacon(url, data);
            };
            if (iframeWin.fetch) {
                const iframeOrigFetch = iframeWin.fetch;
                iframeWin.fetch = function(...args) {
                    let url = typeof args[0] === 'string' ? args[0] : (args[0] && args[0].url ? args[0].url : '');
                    if (url) {
                        try { url = new URL(url, location.origin).href; } catch(e){}
                        const action = applyFilter(url);
                        if (action && action.response) {
                            if (action.response.status === 403) {
                                tmStats.recordBlock(url);
                                return Promise.reject(new Error("Blocked by SSOT iframe sandbox"));
                            } else if (action.response.status === 204) {
                                tmStats.recordDrop(url);
                                return Promise.resolve(new Response(null, { status: 204, statusText: 'No Content' }));
                            }
                        }
                    }
                    return iframeOrigFetch.apply(this, args);
                };
            }
        } catch(e) {}
    }

    const origCreateElement = document.createElement.bind(document);
    document.createElement = function(tagName, options) {
        const el = origCreateElement(tagName, options);
        if (tagName && tagName.toLowerCase() === 'iframe') {
            el.addEventListener('load', () => patchIframeBeacon(el), { once: false });
        }
        return el;
    };
    try {
        const existingIframes = document.querySelectorAll('iframe');
        for (const iframe of existingIframes) patchIframeBeacon(iframe);
    } catch(e) {}

    document.addEventListener('click', (e) => {
        const target = e.target.closest('a[ping]');
        if (target) {
            target.removeAttribute('ping');
            if (CONFIG.DEBUG_MODE) console.log(`[SSOT-TM] 🔪 Ping Attribute Defused on click`);
        }
    }, true);

    function defuseAllPingAttributes(root) {
        try {
            const anchors = (root || document).querySelectorAll('a[ping]');
            for (const a of anchors) {
                a.removeAttribute('ping');
            }
        } catch(e) {}
    }

    const CSS_BG_URL_RE = /url\s*\(\s*['"]?(https?:\/\/[^'")\s]+)['"]?\s*\)/gi;
    function defuseCssBgTrackers(node) {
        try {
            if (!node || !node.style || !node.style.backgroundImage) return;
            const bgVal = node.style.backgroundImage;
            let match;
            CSS_BG_URL_RE.lastIndex = 0;
            while ((match = CSS_BG_URL_RE.exec(bgVal)) !== null) {
                const action = applyFilter(match[1]);
                if (action && action.response) {
                    node.style.backgroundImage = 'none';
                    if (action.response.status === 403) tmStats.recordBlock(match[1]);
                    else if (action.response.status === 204) tmStats.recordDrop(match[1]);
                    if (CONFIG.DEBUG_MODE) console.log(`[SSOT-TM] 🎨 CSS bg-image tracker defused: ${match[1]}`);
                    break;
                }
            }
        } catch(e) {}
    }

    const observer = new MutationObserver((mutations) => {
        for (const mutation of mutations) {
            for (const node of mutation.addedNodes) {
                if (node.nodeType !== 1) continue; 

                if (node.tagName === 'A' && node.hasAttribute('ping')) {
                    node.removeAttribute('ping');
                } else if (node.querySelectorAll) {
                    defuseAllPingAttributes(node);
                }

                defuseCssBgTrackers(node);
                if (node.querySelectorAll) {
                    try {
                        const styled = node.querySelectorAll('[style*="background"]');
                        for (const el of styled) defuseCssBgTrackers(el);
                    } catch(e) {}
                }

                if (node.tagName === 'IFRAME') {
                    node.addEventListener('load', () => patchIframeBeacon(node), { once: false });
                    patchIframeBeacon(node); 
                }
                
                // 保留 MutationObserver 作為安全網 (針對不支援 property hook 的邊界情況)
                if (node.tagName === 'SCRIPT' || node.tagName === 'IMG' || node.tagName === 'IFRAME') {
                    if (node.src) {
                        try {
                            const action = applyFilter(node.src);
                            if (action && action.response) {
                                if (action.response.status === 403) {
                                    tmStats.recordBlock(node.src);
                                    node.remove();
                                } else if (action.response.status === 204) {
                                    tmStats.recordDrop(node.src);
                                    node.remove();
                                }
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
            defuseAllPingAttributes(document); 
            observer.observe(document.documentElement, { childList: true, subtree: true, attributes: true, attributeFilter: ['ping', 'style', 'src'] });
            initUI();
        });
    } else {
        defuseAllPingAttributes(document); 
        observer.observe(document.documentElement, { childList: true, subtree: true, attributes: true, attributeFilter: ['ping', 'style', 'src'] });
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
    
    _map_drop_domains = {d for d, paths in RULES_DB["CRITICAL_PATH_MAP"].items() if any(p == 'DROP:/' for p in paths)}

    for d in RULES_DB["BLOCK_DOMAINS"]:
        has_map_drop = d in _map_drop_domains
        expected = RES_ALLOW if is_domain_whitelisted(d) else (RES_DROP_204 if has_map_drop else RES_BLOCK_403)
        cases.append(TestCase("Auto: Domain Block", f"https://{d}/test", expected, "Blocked by Domain" + (" (MAP DROP)" if has_map_drop else "")))
    for d in RULES_DB["BLOCK_DOMAINS_WILDCARDS"]:
        has_map_drop = d in _map_drop_domains
        expected_exact = RES_ALLOW if is_domain_whitelisted(d) else (RES_DROP_204 if has_map_drop else RES_BLOCK_403)
        cases.append(TestCase("Auto: Domain Block WC (Exact)", f"https://{d}/test", expected_exact, "Blocked by Wildcard Domain" + (" (MAP DROP)" if has_map_drop else "")))
        sub = f"sub.{d}"
        expected_sub = RES_ALLOW if is_domain_whitelisted(sub) else (RES_DROP_204 if has_map_drop else RES_BLOCK_403)
        cases.append(TestCase("Auto: Domain Block WC (Sub)", f"https://{sub}/test", expected_sub, "Blocked by Wildcard Subdomain" + (" (MAP DROP)" if has_map_drop else "")))

    for d in RULES_DB["REDIRECTOR_HOSTS"]:
        cases.append(TestCase("Auto: Redirector", f"https://{d}/target", RES_BLOCK_403, "Blocked Redirector"))

    for d in RULES_DB["REDIRECT_EXTRACT_HOSTS"]:
        cases.append(TestCase("Auto: Redirect Extract (Target)", f"https://{d}/https%3A%2F%2Fwww.example.com%2Fpage", RES_CLEAN_302, "Redirect Extract: decoded target URL → 302"))
        cases.append(TestCase("Auto: Redirect Extract (Asset Block)", f"https://{d}/style.css", RES_BLOCK_403, "Redirect Extract: non-URL asset blocked → 403"))
        cases.append(TestCase("Auto: Redirect Extract (Query Param)", f"https://{d}/?id=725X1342&url=https%3A%2F%2Fwww.example.com%2Fpage&xs=1", RES_CLEAN_302, "Redirect Extract: ?url= query param → 302"))

    _cpm_keys = set(RULES_DB["CRITICAL_PATH_MAP"].keys())
    for hostname, paths in RULES_DB["CRITICAL_PATH_MAP"].items():
        # Determine if any parent domain is also in MAP (subdomain would inherit parent, not this entry)
        _hostname_parts = hostname.split('.')
        _parent_in_map = any(
            '.'.join(_hostname_parts[i:]) in _cpm_keys
            for i in range(1, len(_hostname_parts))
        )
        for p in paths:
            if p.startswith("DROP:"):
                clean_path = p[5:]
                url_base = f"https://{hostname}" + (clean_path if clean_path.startswith("/") else f"/{clean_path}")
                cases.append(TestCase("Auto: Critical Map (Drop Routing)", url_base, RES_DROP_204, "Action Routing 支援 DROP 權重解析"))
                if not _parent_in_map:
                    sub_url = f"https://sub.{hostname}" + (clean_path if clean_path.startswith("/") else f"/{clean_path}")
                    cases.append(TestCase("Auto: Critical Map Subdomain (Drop)", sub_url, RES_DROP_204, f"子域名繼承 MAP DROP 規則: sub.{hostname}"))
            else:
                url_base = f"https://{hostname}" + (p if p.startswith("/") else f"/{p}")
                expected = RES_DROP_204 if "CheckConnection" in p else RES_BLOCK_403
                cases.append(TestCase("Auto: Critical Map", url_base, expected, "Blocked by Map"))
                if not _parent_in_map:
                    sub_url = f"https://sub.{hostname}" + (p if p.startswith("/") else f"/{p}")
                    cases.append(TestCase("Auto: Critical Map Subdomain", sub_url, expected, f"子域名繼承 MAP 封鎖規則: sub.{hostname}"))

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

    _priority_drop_lower = [k.lower() for k in RULES_DB["PRIORITY_DROP"]]
    for p in RULES_DB["CRITICAL_PATH_GENERIC"]:
        path_lower_check = (p if p.startswith('/') else '/' + p).lower()
        priority_drop_fires_first = any(k in path_lower_check for k in _priority_drop_lower)
        if priority_drop_fires_first or "CheckConnection" in p:
            expected = RES_DROP_204
        else:
            expected = RES_BLOCK_403
        cases.append(TestCase("Auto: Critical Path", f"https://example.com{p if p.startswith('/') else '/' + p}", expected, "Blocked by L1"))

    static_suffixes = RULES_DB["EXCEPTIONS_SUFFIXES"]
    _critical_lower = [c.lower() for c in RULES_DB["CRITICAL_PATH_GENERIC"] + RULES_DB["CRITICAL_PATH_SCRIPT_ROOTS"]]
    for k in RULES_DB["DROP"] + RULES_DB["PRIORITY_DROP"]:
        if any(k.endswith(s) for s in static_suffixes if s.startswith('.')): continue
        test_path = f"/log/{k.replace('/', '')}"
        test_path_lower = test_path.lower()
        # Skip if a CRITICAL_PATH (L1 block) or PATH_BLOCK keyword fires before DROP
        if any(c in test_path_lower for c in _critical_lower): continue
        if is_path_keyword_blocked(test_path): continue
        cases.append(TestCase("Auto: Keyword Drop", f"https://example.com{test_path}", RES_DROP_204, "Silent Drop"))

    for p in RULES_DB["PARAMS_GLOBAL"]:
         test_path = f"/?{p}=test"
         # If the param name itself is a path-block keyword, the engine blocks before cleaning
         expected_neutral = RES_BLOCK_403 if is_path_keyword_blocked(test_path) else RES_CLEAN_302
         cases.append(TestCase("Privacy: Clean (Neutral)", f"https://example.com{test_path}", expected_neutral, "Param Cleaning"))
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
    cases.append(TestCase("Privacy: OTel Log Drop", "https://pbd.yahoo.com/otel/v1/logs", RES_DROP_204, "V44.37 OTLP Log Silent Drop (Elevated precedence)"))
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

    cases.append(TestCase("Privacy: Slack Telemetry Drop", "https://clorastech.slack.com/clog/track/?data=1", RES_DROP_204, "V44.88 Action Routing 支援 DROP 權重解析並驗證 204"))

    # --- V44.79 104 APP 反向排除機制測試 ---
    cases.append(TestCase("Strategy: 104 App Track API", "https://appapi.104.com.tw/2.0/track/company/post/view?device_id=TEST_ID", RES_ALLOW, "寬鬆放行 /2.0/ 目錄下未知業務路徑之 device_id"))
    cases.append(TestCase("Strategy: 104 App Subscription API", "https://appapi.104.com.tw/2.0/subscription/news?device_id=TEST_ID", RES_ALLOW, "寬鬆放行 /2.0/ 目錄下未知業務路徑之 device_id"))
    cases.append(TestCase("Strategy: 104 App Ad Override", "https://appapi.104.com.tw/2.0/ad/search/hashtag?device_id=TEST_ID", RES_REWRITE, "驗證 !/2.0/ad/ 絕對否決標籤成功狙擊廣告模組"))

    # --- V44.80 風傳媒 ChunkLoadError 防護 ---
    cases.append(TestCase("BugFix: Storm Media ChunkLoadError", "https://www.storm.mg/_nuxt/track.20260312-151014.BRJtw5_7.js", RES_ALLOW, "放行風傳媒追蹤腳本以避免 Vue Router 觸發 404 重定向防護網"))

    # --- V44.82 Uber Eats GraphQL 批次請求破圖修復測試 ---
    cases.append(TestCase("BugFix: Uber Eats GraphQL Batching", "https://helix-go-webview.uber.com/go/_events", RES_ALLOW, "放行 Uber Eats GraphQL 遙測與業務混合端點以修復菜單破圖"))
    
    # --- V44.83 Foodpanda 動作路由 (靜默拋棄) 測試 ---
    cases.append(TestCase("Strategy: Foodpanda Action Log Drop", "https://tw.fd-api.com/api/v5/action-log?device_id=test", RES_DROP_204, "將 Foodpanda 遙測升級為 204 靜默拋棄，徹底避免 APP 重試風暴"))

    # --- V44.87 Yahoo! JAPAN 跨站點 Cookie 同步測試 ---
    cases.append(TestCase("Privacy: Audience Cookie Sync", "https://aai.yahooapis.jp/v2/acookie/lookup?appid=TEST&type=2&priority=0", RES_BLOCK_403, "精準攔截 Yahoo JP 跨站點 Cookie 同步 API，避免誤殺整段網域"))
    cases.append(TestCase("Edge: Yahoo API Safe Harbor", "https://map.yahooapis.jp/search/local/V1/localSearch?appid=TEST", RES_ALLOW, "確保 yahooapis.jp 的正常地圖 API 不被誤殺"))

    # --- V44.89 Teams & Discord 204 DROP 測試 ---
    cases.append(TestCase("Strategy: Teams Event Telemetry Drop", "https://browser.events.data.microsoft.com/OneCollector/1.0", RES_DROP_204, "將 Teams 高頻遙測從 P0 網域轉移至 204 DROP 拋棄"))
    cases.append(TestCase("Strategy: Discord Science Telemetry Drop", "https://discord.com/api/v9/science", RES_DROP_204, "將 Discord v9/v10 科學大數據遙測轉換為 204 靜默拋棄"))

    # --- V44.94 slackb.com 全域 204 DROP 測試 ---
    cases.append(TestCase("Strategy: Slackb Traces Drop", "https://slackb.com/traces/v1/list_of_spans/json", RES_DROP_204, "slackb.com 純遙測域名從 P0 BLOCK 升級為全域 204 DROP，消除 Slack 重試風暴"))
    cases.append(TestCase("Strategy: Slackb Any Path Drop", "https://slackb.com/api/v1/events", RES_DROP_204, "slackb.com 所有路徑均 DROP:/  全域捕捉"))
    cases.append(TestCase("Strategy: Slackb Root Drop", "https://slackb.com/test", RES_DROP_204, "slackb.com 根路徑亦觸發 204 DROP"))

    # --- V44.92 Slack EventLog 204 DROP + BusinessToday GAD 腳本攔截測試 ---
    cases.append(TestCase("Strategy: Slack EventLog History Drop", "https://slack.com/api/eventlog.history", RES_DROP_204, "精準攔截 Slack 事件日誌 API，204 靜默拋棄避免企業軟體重試風暴"))
    cases.append(TestCase("AdBlock: BusinessToday GAD Script", "https://www.businesstoday.com.tw/lazyweb/web/js/gad/gad_script.js?v=431414276", RES_BLOCK_403, "L1 Scanner 無條件攔截 gad_script. 廣告腳本，不受 /js/ 靜態豁免影響"))
    cases.append(TestCase("BugFix: BusinessToday Google News Image", "https://www.businesstoday.com.tw/lazyweb/web/img/google%20news-2.jpg", RES_ALLOW, "Google News 品牌圖片為正常靜態資源，.jpg + /img/ 路徑應放行"))

    # --- V44.96+ 104 APP /apis/ 命名空間豁免測試 ---
    cases.append(TestCase("BugFix: 104 App /apis/ Exact Match", "https://appapi.104.com.tw/apis/resume/v3/list/front?device_type=0&device_id=TEST_ID", RES_ALLOW, "精準命中局部豁免，保留 device_id"))
    cases.append(TestCase("BugFix: 104 App /apis/ Unauthorized Param", "https://appapi.104.com.tw/apis/resume/v3/list/front?device_id=TEST_ID&utm_source=fb", RES_REWRITE, "保留 device_id，精確剝離未授權之 utm_source"))
    cases.append(TestCase("BugFix: 104 App /apis/ Case Insensitive", "https://appapi.104.com.tw/APIs/resume/v3/list?device_id=TEST", RES_ALLOW, "大小寫不敏感，強制小寫化後匹配放行"))
    cases.append(TestCase("Strategy: 104 App /apis/ad/ Future Block", "https://appapi.104.com.tw/apis/ad/banner?device_id=TEST", RES_ALLOW, "若未來新增廣告端點，預設放行 device_id（可透過 !/apis/ad/ 否決）"))
    
    # --- V45.01 Anthropic (Claude) 第一方代理遙測攔截測試 ---
    cases.append(TestCase("Strategy: Anthropic Statsig Drop", "https://statsig.anthropic.com/v1/rgstr", RES_DROP_204, "V45.01 將 Anthropic 第一方代理遙測端點設定為 204 靜默拋棄以避免重試風暴"))

    # --- V45.02 Clipboard Interceptor (剪貼簿攔截器) Feedly URL 測試 ---
    cases.append(TestCase("Privacy: Feedly Share UTM Strip", "https://unwire.hk/2026/03/23/article/fun-tech/?utm_source=feedly&utm_medium=rss", RES_CLEAN_302, "驗證來自 Feedly App 帶有 UTM 參數的髒連結，在放入剪貼簿前能被 SSOT 引擎精確剝離"))

    # --- V45.03 台灣在地聯播網與 WordPress 盲區縫合測試 ---
    cases.append(TestCase("AdBlock: Taiwan RTB (Ad2iction)", "https://cdn2.ad2n.com/", RES_BLOCK_403, "精準封鎖艾迪英特廣告商 CDN 遞送端點"))
    cases.append(TestCase("AdBlock: WP Ads Plugin (Quick AdSense)", "https://axiang.cc/wp-content/plugins/quick-adsense-reloaded/assets/js/ads.js?ver=2.0.98.1", RES_BLOCK_403, "完美縫合 WordPress 外掛的 assets/js 靜態保護傘，強制攔截惡意 ads.js"))
    cases.append(TestCase("AdBlock: Ad Inserter Plugin", "https://example.com/wp-content/plugins/ad-inserter/js/ad-inserter.js", RES_BLOCK_403, "透過 Raw Regex 精準命中 ad-inserter 外掛特徵"))
    cases.append(TestCase("AdBlock: adsbygoogle Nested Path", "https://axiang.cc/%22https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=123", RES_BLOCK_403, "透過 Raw Regex 成功識別前端渲染錯誤造成的 adsbygoogle 路徑嵌套漏洞"))
    cases.append(TestCase("Safe: Non-Ad Script (uploads.js)", "https://example.com/assets/js/uploads.js?v=1", RES_ALLOW, r"驗證 Raw Regex 邊界符號 (?:\\?|$) 有效，確保不會因為字尾包含 ads.js 而誤殺正常的上傳模組"))

    # --- V45.05 網域輪替防護與 Adbot 在地聯播網測試 ---
    cases.append(TestCase("AdBlock: Anti-Adblock Rotation", "https://adunblock2.static-cloudflare.workers.dev/script.js", RES_BLOCK_403, "攔截 Serverless 反廣告攔截腳本的動態網域輪替"))
    cases.append(TestCase("AdBlock: Anti-Adblock Ext", "https://adunblock99-beta.static-cloudflare.workers.dev/script.js", RES_BLOCK_403, "驗證放寬後的正則能捕捉 adunblock 變體"))
    cases.append(TestCase("AdBlock: Micro Local RTB", "https://cell1.adbottw.net/dy/native/?ca=achang.tw_rec", RES_BLOCK_403, "精準攔截台灣在地微型原生廣告聯播網 (Adbot)"))

    cases.append(TestCase("E2E: Payload Fetch", "https://static.104.com.tw/104main/jb/area/manjb/home/json/jobNotify/ad.json?v=1772752285970", RES_ALLOW, "確保第一階段資料層 UI 放行不破圖"))
    cases.append(TestCase("E2E: Internal Nav Rewrite", "https://static.104.com.tw/ad.json", RES_REWRITE, "模擬擷取 JSON 後點擊，觸發第二階段靜默重寫", is_e2e=True, e2e_target_url="https://guide.104.com.tw/career/compare/major/?utm_source=104&utm_medium=whitebar"))
    cases.append(TestCase("E2E: Malicious Payload Block", "https://static.104.com.tw/ad.json", RES_BLOCK_403, "模擬 JSON 內遭植入第三方追蹤並點擊，觸發 L1 攔截", is_e2e=True, e2e_target_url="https://googleadservices.com/track/click"))
    cases.append(TestCase("E2E: URL Fragment Bypass", "https://static.104.com.tw/ad.json", RES_ALLOW, "模擬 HTTP Hash 參數剝離物理限制", is_e2e=True, e2e_target_url="https://guide.104.com.tw/#/test?fbclid=123"))

    # --- V45.18-19 遙測拋棄機制 ---
    cases.append(TestCase("Privacy: Optimizely Event Telemetry (iHerb)", "https://logx.optimizely.com/v1/events", RES_DROP_204, "iHerb App 瘋狂打的 Optimizely 事件端點，MAP DROP 前置攔截避免 403 重試風暴"))
    cases.append(TestCase("Privacy: Alexa Metrics (CDN Parasite)", "https://d31qbv1cthcecs.cloudfront.net/atrk.js", RES_BLOCK_403, "精準命中 L1 掃描，強制阻斷寄生於 CDN 的追蹤腳本"))
    cases.append(TestCase("Privacy: 91APP Telemetry Drop", "https://cpdl-deferrer.91app.com/api/v1/deferrer-log?env=prod&size=393x852", RES_DROP_204, "V45.19 將 91APP 專有遙測升級為 204 靜默拋棄，阻斷硬體指紋收集"))
    cases.append(TestCase("Safe: 91APP Business API", "https://shopapi.91app.com/v1/cart/items", RES_ALLOW, "V45.19 確保 91APP 的正常電商業務端點不被誤殺"))

    # --- V45.20 雙軌阻擋策略 (App Insights & Sift Science) ---
    cases.append(TestCase("Privacy: App Insights Script", "https://az416426.vo.msecnd.net/scripts/a/ai.0.js", RES_BLOCK_403, "V45.20 物理阻斷微軟 App Insights 遙測腳本"))
    cases.append(TestCase("Privacy: Sift Science Drop", "https://api3.siftscience.com/v3/accounts/64e6742e35ba4d3981f27c05/mobile_events", RES_DROP_204, "V45.20 靜默拋棄 Sift Science 行為生物特徵遙測"))

    # --- V45.21 Vercel Insights 第一方代理防護 ---
    cases.append(TestCase("Privacy: Vercel Insights Script", "https://www.xanswer.com/_vercel/insights/script.js", RES_BLOCK_403, "V45.21 第一方代理防護：L1 掃描器精準突破 script.js 靜態保護傘實施 403 阻斷"))
    cases.append(TestCase("Privacy: Vercel Speed Insights", "https://www.xanswer.com/_vercel/speed-insights/vitals", RES_BLOCK_403, "V45.21 阻斷 Core Web Vitals 第一方代理回傳端點"))
    cases.append(TestCase("Safe: Common script.js", "https://www.xanswer.com/assets/js/script.js", RES_ALLOW, "V45.21 確保常規命名之 script.js 依然受惠於靜態豁免不被誤殺"))
    cases.append(TestCase("Safe: Next.js Core Chunks", "https://www.xanswer.com/_next/static/chunks/main.js", RES_ALLOW, "V45.21 確保 Next.js 核心水合 (Hydration) 靜態資源安全放行"))

    # --- V45.22 Vercel 遙測 CDN 全域封堵 + 現代圖片格式追蹤像素 ---
    cases.append(TestCase("Privacy: Vercel Scripts CDN (Analytics)", "https://va.vercel-scripts.com/v1/script.js", RES_BLOCK_403, "V45.22 封堵 Vercel 主要 CDN 供應的 Web Analytics 追蹤腳本"))
    cases.append(TestCase("Privacy: Vercel Scripts CDN (Speed Insights)", "https://va.vercel-scripts.com/v1/speed-insights/script.js", RES_BLOCK_403, "V45.22 封堵 Vercel CDN 供應的 Speed Insights 性能遙測腳本"))
    cases.append(TestCase("Privacy: Vercel Scripts CDN (Debug)", "https://va.vercel-scripts.com/v1/script.debug.js", RES_BLOCK_403, "V45.22 封堵 Vercel CDN 的 debug 模式追蹤腳本"))
    cases.append(TestCase("Privacy: Vercel Insights CDN (HTML)", "https://cdn.vercel-insights.com/v1/script.js", RES_BLOCK_403, "V45.22 封堵 HTML-only 整合使用的 Vercel Insights CDN 腳本"))
    cases.append(TestCase("Privacy: Vercel Analytics Vitals", "https://vitals.vercel-analytics.com/v1/vitals", RES_BLOCK_403, "V45.22 封堵 Vercel Speed Insights 替代性 vitals 回報域名"))
    cases.append(TestCase("Privacy: WebP Tracking Pixel", "https://tracker.example.com/pixel.webp", RES_BLOCK_403, "V45.22 現代圖片格式追蹤像素防護：WebP 偽裝"))
    cases.append(TestCase("Privacy: SVG Tracking Beacon", "https://tracker.example.com/beacon.svg", RES_BLOCK_403, "V45.22 現代圖片格式追蹤像素防護：SVG 偽裝"))

    # --- V45.23 第一方代理遙測偽裝：跨平台分析服務 CDN 封堵 ---
    cases.append(TestCase("Privacy: PostHog US Ingestion", "https://us.i.posthog.com/batch", RES_BLOCK_403, "V45.23 封堵 PostHog 美區事件攝取端點，阻斷第一方代理回傳"))
    cases.append(TestCase("Privacy: PostHog EU Ingestion", "https://eu.i.posthog.com/i/v0/e", RES_BLOCK_403, "V45.23 封堵 PostHog 歐區 v0 事件攝取端點"))
    cases.append(TestCase("Privacy: PostHog US Assets", "https://us-assets.i.posthog.com/static/array.js", RES_BLOCK_403, "V45.23 封堵 PostHog 美區 SDK 靜態腳本 CDN"))
    cases.append(TestCase("Privacy: PostHog EU Assets", "https://eu-assets.i.posthog.com/static/array.js", RES_BLOCK_403, "V45.23 封堵 PostHog 歐區 SDK 靜態腳本 CDN"))
    cases.append(TestCase("Privacy: Simple Analytics CDN", "https://scripts.simpleanalyticscdn.com/latest.js", RES_BLOCK_403, "V45.23 封堵 Simple Analytics 腳本 CDN"))
    cases.append(TestCase("Privacy: Simple Analytics Queue", "https://queue.simpleanalyticscdn.com/noscript.gif", RES_BLOCK_403, "V45.23 封堵 Simple Analytics 無腳本追蹤像素"))
    cases.append(TestCase("Privacy: Simple Analytics Proxy", "https://simpleanalyticsexternal.com/proxy.js", RES_BLOCK_403, "V45.23 封堵 Simple Analytics 外部代理腳本"))
    cases.append(TestCase("Privacy: Fathom CDN Script", "https://cdn.usefathom.com/script.js", RES_BLOCK_403, "V45.23 封堵 Fathom Analytics CDN 追蹤腳本"))
    cases.append(TestCase("Privacy: Pirsch Analytics API", "https://api.pirsch.io/pa.js", RES_BLOCK_403, "V45.23 封堵 Pirsch Analytics API 追蹤腳本"))
    cases.append(TestCase("Privacy: Pirsch Analytics Hit", "https://api.pirsch.io/api/v1/hit", RES_BLOCK_403, "V45.23 封堵 Pirsch Analytics 頁面瀏覽回報端點"))

    # --- V45.24 台灣特有第一方代理遙測偽裝封堵 ---
    cases.append(TestCase("Privacy: Dcard Ads Pixel", "https://pixel.dcard.tw/event?client_id=abc123", RES_BLOCK_403, "V45.24 封堵 Dcard 廣告追蹤像素端點 (台灣最大匿名論壇)"))
    cases.append(TestCase("Privacy: Dcard Ads SDK", "https://assets.dcard.tw/scripts/web-ad-tracking-sdk/latest.js", RES_BLOCK_403, "V45.24 封堵 Dcard 廣告追蹤 SDK 腳本 CDN"))
    cases.append(TestCase("Safe: Dcard Static Assets", "https://assets.dcard.tw/images/logo.svg", RES_ALLOW, "V45.24 確保 Dcard 正常靜態資源 (圖片/CSS) 不被誤殺"))
    cases.append(TestCase("Privacy: Insider Tracking", "https://eva.api.useinsider.com/ins.js?id=10001", RES_BLOCK_403, "V45.24 封堵 Insider 個人化追蹤腳本 (台灣 EVA Air/Carrefour/Watsons 等品牌使用)"))
    cases.append(TestCase("Privacy: Insider API Track", "https://momo.api.useinsider.com/track", RES_BLOCK_403, "V45.24 封堵 Insider 事件回報端點 (台灣 momo 使用)"))
    cases.append(TestCase("Privacy: GrowingIO CDN Script", "https://assets.giocdn.com/2.1/gio.js", RES_BLOCK_403, "V45.24 封堵 GrowingIO 分析腳本 CDN"))
    cases.append(TestCase("Privacy: GrowingIO CDP Script", "https://assets.giocdn.com/cdp/1.0/gio.js", RES_BLOCK_403, "V45.24 封堵 GrowingIO CDP 分析腳本 CDN"))

    # --- V45.25 主流分析平台逃逸 CDN 域名封堵 ---
    cases.append(TestCase("Privacy: Amplitude CDN Script", "https://cdn.amplitude.com/script/abc123key.js", RES_BLOCK_403, "V45.25 封堵 Amplitude 腳本 CDN (從主域名 BLOCK_DOMAINS 逃逸的子域名)"))
    cases.append(TestCase("Privacy: Amplitude EU CDN", "https://cdn.eu.amplitude.com/script/abc123key.js", RES_BLOCK_403, "V45.25 封堵 Amplitude EU 區腳本 CDN"))
    cases.append(TestCase("Privacy: Amplitude API2", "https://api2.amplitude.com/2/httpapi", RES_BLOCK_403, "V45.25 封堵 Amplitude 替代 API 端點 (api2 非 api)"))
    cases.append(TestCase("Privacy: Amplitude Batch API", "https://api2.amplitude.com/batch", RES_BLOCK_403, "V45.25 封堵 Amplitude 批次上傳 API"))
    cases.append(TestCase("Privacy: Amplitude EU API", "https://api.eu.amplitude.com/2/httpapi", RES_BLOCK_403, "V45.25 封堵 Amplitude EU 區 API 端點"))
    cases.append(TestCase("Privacy: Mixpanel CDN", "https://cdn.mxpnl.com/libs/mixpanel-2-latest.min.js", RES_BLOCK_403, "V45.25 封堵 Mixpanel 腳本 CDN (完全不同域名 mxpnl.com)"))
    cases.append(TestCase("Privacy: Mixpanel Decide", "https://decide.mixpanel.com/decide?verbose=1", RES_BLOCK_403, "V45.25 封堵 Mixpanel decide 配置端點"))
    cases.append(TestCase("Privacy: Heap Analytics CDN", "https://cdn.heapanalytics.com/js/heap-abc123.js", RES_BLOCK_403, "V45.25 封堵 Heap 腳本 CDN (不同於 heap.io)"))
    cases.append(TestCase("Privacy: Heap API CDN", "https://cdn.us.heap-api.com/config/abc123.json", RES_BLOCK_403, "V45.25 封堵 Heap API CDN 配置端點"))
    cases.append(TestCase("Privacy: RudderStack CDN", "https://cdn.rudderlabs.com/v1.1/rudder-analytics.min.js", RES_BLOCK_403, "V45.25 封堵 RudderStack SDK CDN (不同於 rudderstack.com)"))
    cases.append(TestCase("Privacy: Segment EU API", "https://eu1.api.segmentapis.com/v1/track", RES_BLOCK_403, "V45.25 封堵 Segment EU API (不同於 segment.com/segment.io)"))

    # --- V45.26 台灣地區擴充：LINE Tag / Treasure Data / Pixnet / 台灣廣告聯播網替代域名 ---
    cases.append(TestCase("Privacy: LINE Tag Script", "https://d.line-scdn.net/n/line_tag/public/release/v1/lt.js", RES_BLOCK_403, "V45.26 精準路徑攔截 LINE Tag 追蹤腳本 (不封鎖整個 line-scdn.net CDN)"))
    cases.append(TestCase("Safe: LINE Sticker CDN", "https://d.line-scdn.net/sticker/12345/main.png", RES_ALLOW, "V45.26 確保 LINE 貼圖/內容 CDN 不被誤殺"))
    cases.append(TestCase("Privacy: LINE Conversion Pixel", "https://tr.line.me/tag.gif?pid=abc123", RES_BLOCK_403, "V45.26 封堵 LINE 轉換追蹤像素端點"))
    cases.append(TestCase("Privacy: Treasure Data CDN", "https://cdn.treasuredata.com/sdk/4.4/td.min.js", RES_BLOCK_403, "V45.26 封堵 Treasure Data JS SDK CDN (台灣企業級 CDP)"))
    cases.append(TestCase("Privacy: Treasure Data Ingest", "https://in.treasuredata.com/js/v3/event/abc123", RES_BLOCK_403, "V45.26 封堵 Treasure Data 資料攝取端點"))
    cases.append(TestCase("Privacy: Treasure Data Alt", "https://cdp.in.treasure-data.com/v1/collect", RES_BLOCK_403, "V45.26 封堵 Treasure Data 替代域名"))
    cases.append(TestCase("Privacy: InsiderOne API", "https://developers.insiderone.com/api/track", RES_BLOCK_403, "V45.26 封堵 Insider 新品牌域名 (繞過 useinsider.com 封鎖)"))
    cases.append(TestCase("Privacy: Tagtoo TW DXP", "https://dxp.tagtoo.com.tw/api/event", RES_BLOCK_403, "V45.26 封堵 Tagtoo 台灣主域名 (僅 tagtoo.co 被封鎖)"))
    cases.append(TestCase("Privacy: Scupio Alt Domain", "https://ad.scupio.net/prebid", RES_BLOCK_403, "V45.26 封堵 Scupio/Bridgewell 替代域名"))
    cases.append(TestCase("Privacy: ClickForce Alt", "https://track.clickforce.net/pixel", RES_BLOCK_403, "V45.26 封堵 ClickForce 替代域名"))
    cases.append(TestCase("Privacy: OneAD OneVision", "https://pixel.onevision.com.tw/track", RES_BLOCK_403, "V45.26 封堵 OneAD OneVision 子品牌追蹤"))
    cases.append(TestCase("Privacy: Pixnet Analytics", "https://s.pixanalytics.com/c.js", RES_BLOCK_403, "V45.26 封堵 Pixnet 部落格分析 CDN 腳本"))
    cases.append(TestCase("Privacy: Pixnet Plugin", "https://referer.pixplug.in/static/r.js", RES_BLOCK_403, "V45.26 封堵 Pixnet 來源追蹤插件"))

    # --- V45.27 阿里雲 SLS 遙測盲區封堵 + Google Play 遙測路徑攔截 ---
    cases.append(TestCase("Privacy: Alibaba SLS Telemetry", "https://zpqy.cn-wulanchabu.log.aliyuncs.com/logstores/web-tracking/track?APIVersion=0.6.0", RES_BLOCK_403, "V45.27 封堵阿里雲 SLS (Simple Log Service) 遙測端點 — 烏蘭察布區域實例"))
    cases.append(TestCase("Privacy: Alibaba SLS Shanghai", "https://myproject.cn-shanghai.log.aliyuncs.com/logstores/access-log/track", RES_BLOCK_403, "V45.27 阿里雲 SLS 萬用字元覆蓋所有區域 (上海實例)"))
    cases.append(TestCase("Privacy: Alibaba SLS Hangzhou", "https://app-analytics.cn-hangzhou.log.aliyuncs.com/logstores/user-behavior/track", RES_BLOCK_403, "V45.27 阿里雲 SLS 使用者行為追蹤 (杭州實例)"))
    cases.append(TestCase("Privacy: Alibaba SLS Global", "https://overseas.ap-southeast-1.log.aliyuncs.com/logstores/events/track", RES_BLOCK_403, "V45.27 阿里雲 SLS 海外區域覆蓋 (新加坡實例)"))
    cases.append(TestCase("Privacy: Alibaba SLS Ingest", "https://data.cn-beijing.sls.aliyuncs.com/logstores/telemetry/track", RES_BLOCK_403, "V45.27 封堵阿里雲 SLS 替代端點 (sls.aliyuncs.com)"))
    cases.append(TestCase("Safe: Alibaba Cloud Non-SLS", "https://oss-cn-hangzhou.aliyuncs.com/bucket/image.jpg", RES_ALLOW, "V45.27 確保阿里雲 OSS 等非 SLS 服務不被誤殺"))
    cases.append(TestCase("Safe: Qianwen AI Whitelist", "https://qianwen.aliyun.com/chat", RES_ALLOW, "V45.27 確保通義千問 AI 硬白名單不受影響 (aliyun.com ≠ aliyuncs.com)"))
    cases.append(TestCase("Privacy: Google Play Telemetry", "https://play.google.com/log?hasfast=true&authuser=0&format=json", RES_BLOCK_403, "V45.27 封堵 Google Play Store 遙測日誌端點 (/log)"))
    cases.append(TestCase("Privacy: Google Play Log Auth", "https://play.google.com/log?hasfast=true&auth=SAPISIDHASH%2Ba182854a&format=json", RES_BLOCK_403, "V45.27 封堵 Google Play 帶 SAPISIDHASH 認證令牌的遙測請求"))
    cases.append(TestCase("Safe: Google Play Store", "https://play.google.com/store/apps/details?id=com.example.app", RES_ALLOW, "V45.27 確保 Google Play 商店正常頁面不被誤殺"))

    # --- V45.28 中國推送 SDK 靜默拋棄升級：防止重試風暴 ---
    cases.append(TestCase("Privacy: JPush SDK Drop", "https://sdk-jmlink.jpush.cn/v1/push?device_id=abc123", RES_DROP_204, "V45.28 極光推送 SDK 升級為 204 靜默拋棄，防止 AlarmManager 重試風暴"))
    cases.append(TestCase("Privacy: JPush User API Drop", "https://user.jpush.cn/v3/device?registration_id=test", RES_DROP_204, "V45.28 極光推送用戶 API 靜默拋棄 (子域名繼承 MAP DROP)"))
    cases.append(TestCase("Privacy: JPush Hash Subdomain Drop", "https://ce3e75d5.jpush.cn/v3/push?uid=test", RES_DROP_204, "V45.28 極光推送動態哈希子域名靜默拋棄"))
    cases.append(TestCase("Privacy: JPush Config Drop", "https://config.jpush.cn/v3/configs?appkey=test", RES_DROP_204, "V45.28 極光推送配置拉取端點靜默拋棄"))
    cases.append(TestCase("Privacy: JPush IO SIS Drop", "https://sis.jpush.io/v1/connect?appkey=test", RES_DROP_204, "V45.32 極光推送 SIS 會話服務 (jpush.io TLD) 靜默拋棄"))
    cases.append(TestCase("Privacy: JPush CN Short Drop", "https://s.jpush.cn/v1/push?rid=test", RES_DROP_204, "V45.32 極光推送短域名已被 jpush.cn 萬用字元覆蓋"))
    cases.append(TestCase("Privacy: Jiguang SDK Drop", "https://sdk.jiguang.cn/v1/report?device=test", RES_DROP_204, "V45.28 極光母品牌 SDK 靜默拋棄"))
    cases.append(TestCase("Privacy: GeTui SDK Drop", "https://gs.getui.com/gbd.action?appid=test", RES_DROP_204, "V45.28 個推 SDK 靜默拋棄 (原 BLOCK_DOMAINS 精確匹配升級)"))
    cases.append(TestCase("Privacy: GeTui Alt Drop", "https://sdk.getui.net/v2/push?cid=test", RES_DROP_204, "V45.28 個推替代域名靜默拋棄"))
    cases.append(TestCase("Privacy: iGexin SDK Drop", "https://sdk.igexin.com/v1/push?appid=test", RES_DROP_204, "V45.28 個推舊品牌 (iGexin) 靜默拋棄"))
    cases.append(TestCase("Privacy: GePush SDK Drop", "https://api.gepush.com/v2/push?token=test", RES_DROP_204, "V45.28 個推推送域名靜默拋棄"))

    # --- V45.29 ChatGLM BDMS 追蹤像素靜默拋棄 ---
    cases.append(TestCase("Privacy: ChatGLM BDMS Pixel Drop", "https://analysis.chatglm.cn/bdms/p.gif?t=1712649600&uid=abc123", RES_DROP_204, "V45.29 智譜清言 BDMS 追蹤像素升級為 204 靜默拋棄，阻斷 SDK 重試風暴"))
    cases.append(TestCase("Privacy: ChatGLM Analytics API Drop", "https://analysis.chatglm.cn/api/v1/event?type=pageview", RES_DROP_204, "V45.29 智譜清言分析 API 端點靜默拋棄"))
    cases.append(TestCase("Privacy: ChatGLM Analytics Collect Drop", "https://analysis.chatglm.cn/collect?data=encoded_payload", RES_DROP_204, "V45.29 智譜清言數據收集端點靜默拋棄"))
    cases.append(TestCase("Safe: ChatGLM Main Service", "https://chatglm.cn/main/alltoolsdetail", RES_ALLOW, "V45.29 確保智譜清言 AI 主服務不受影響 (僅封 analysis. 子域名)"))

    # --- V45.30 微信公眾號遙測精準路徑攔截 ---
    cases.append(TestCase("Privacy: WeChat Article Report Drop", "https://mp.weixin.qq.com/mp/appmsgreport?action=page_time_5s&__biz=MzkwMDU2MTEwMg==&uin=&key=&pass_ticket=&wxtoken=777&devicetype=&clientversion=false", RES_DROP_204, "V45.30 微信公眾號文章閱讀時長回報 (5 秒心跳) 靜默拋棄"))
    cases.append(TestCase("Privacy: WeChat JS Monitor Drop", "https://mp.weixin.qq.com/mp/jsmonitor?idkey=1234_5678&st=1712649600", RES_DROP_204, "V45.30 微信公眾號 JS 效能監控端點靜默拋棄"))
    cases.append(TestCase("Privacy: WeChat WAP Report Drop", "https://mp.weixin.qq.com/mp/wapcommreport?wxtoken=777&report_type=1", RES_DROP_204, "V45.30 微信公眾號 WAP 通用遙測回報靜默拋棄"))
    cases.append(TestCase("Privacy: WeChat Appmsg Report Variant", "https://mp.weixin.qq.com/mp/appmsgreport?action=page_end&__biz=MzkwMDU2MTEwMg==", RES_DROP_204, "V45.30 微信文章回報 action 變體 (page_end) 同樣攔截"))
    cases.append(TestCase("Safe: WeChat Article Content", "https://mp.weixin.qq.com/s/AbCdEfGhIjKlMnOpQrStUv", RES_ALLOW, "V45.30 確保微信公眾號文章內容正常瀏覽不受影響"))
    cases.append(TestCase("Safe: WeChat Article Profile", "https://mp.weixin.qq.com/mp/profile_ext?action=home&__biz=MzkwMDU2MTEwMg==", RES_ALLOW, "V45.30 確保微信公眾號主頁不被誤殺"))

    # =====================================================================
    #  擴展測試矩陣：邊界、變異、優先級衝突、完整覆蓋
    # =====================================================================

    for d in RULES_DB["OAUTH_SAFE_HARBOR_DOMAINS"]:
        if d == 'accounts.youtube.com':
            cases.append(TestCase("Auto: OAuth (YT Exception)", f"https://{d}/page?utm_source=test", RES_CLEAN_302, "accounts.youtube.com 被排除出 OAuth Safe Harbor，非 OAuth 路徑時應淨化參數"))
        else:
            cases.append(TestCase("Auto: OAuth Safe Harbor", f"https://{d}/oauth2/authorize?utm_source=test&state=abc", RES_ALLOW, "OAuth 安全港全面豁免參數淨化"))
    cases.append(TestCase("Edge: OAuth Path Regex", "https://example.com/login?utm_source=test", RES_ALLOW, "OAuth 路徑正則匹配 /login 豁免參數淨化"))
    cases.append(TestCase("Edge: OAuth Path /authorize", "https://example.com/oauth2/authorize?utm_source=test", RES_ALLOW, "OAuth 路徑正則匹配 /oauth2/authorize 豁免參數淨化"))
    cases.append(TestCase("Edge: OAuth Path /signin", "https://example.com/signin?fbclid=test", RES_ALLOW, "OAuth 路徑正則匹配 /signin 豁免參數淨化"))
    cases.append(TestCase("Edge: OAuth Path /session", "https://example.com/session?gclid=test", RES_ALLOW, "OAuth 路徑正則匹配 /session 豁免參數淨化"))

    for d in RULES_DB["ABSOLUTE_BYPASS_DOMAINS"]["EXACT"]:
        cases.append(TestCase("Auto: Absolute Bypass (Exact)", f"https://{d}/api/pay?utm_source=test&fbclid=abc", RES_ALLOW, "絕對繞過域名立即放行，不做任何處理"))
    for d in RULES_DB["ABSOLUTE_BYPASS_DOMAINS"]["WILDCARDS"][:10]:
        cases.append(TestCase("Auto: Absolute Bypass (WC)", f"https://www.{d}/transfer?gclid=test", RES_ALLOW, "萬用字元絕對繞過，子域名繼承"))
    cases.append(TestCase("Edge: Absolute Bypass + Tracking Path", "https://api.ecpay.com.tw/track/pixel?fbclid=123", RES_ALLOW, "絕對繞過優先級高於路徑關鍵字掃描"))

    param_exempt_all = set(RULES_DB["PARAM_CLEANING_EXEMPTED_DOMAINS"]["EXACT"])
    for wc in RULES_DB["PARAM_CLEANING_EXEMPTED_DOMAINS"]["WILDCARDS"]:
        param_exempt_all.add(wc)
    for d in RULES_DB["HARD_WHITELIST"]["EXACT"][:15]:
        is_param_exempt = any(d == e or d.endswith('.' + e) for e in param_exempt_all)
        is_api_prefix = d.startswith('api.') or d.startswith('appapi.')
        if is_param_exempt:
            exp = RES_ALLOW
        elif is_api_prefix:
            exp = RES_REWRITE
        else:
            exp = RES_CLEAN_302
        cases.append(TestCase("Auto: Hard WL (Exact)", f"https://{d}/page?utm_source=test", exp, "硬白名單精確匹配，依子域名決定淨化方式"))

    for d in RULES_DB["SOFT_WHITELIST"]["EXACT"][:10]:
        cases.append(TestCase("Auto: Soft WL (Exact)", f"https://{d}/safe/data", RES_ALLOW, "軟白名單精確匹配，無追蹤參數時直接放行"))
    for d in RULES_DB["SOFT_WHITELIST"]["EXACT"][:5]:
        is_api_prefix = d.startswith('api.') or d.startswith('appapi.')
        exp = RES_REWRITE if is_api_prefix else RES_CLEAN_302
        cases.append(TestCase("Auto: Soft WL + Param", f"https://{d}/page?utm_source=fb", exp, "軟白名單精確匹配，含追蹤參數時依子域名決定淨化方式"))

    # Auto-generated BLOCK_DOMAINS_REGEX coverage — one representative block + one non-match per pattern
    _REGEX_BLOCK_SAMPLES = [
        # (hostname_to_block, hostname_nonmatch, pattern_note)
        ("ads.ettoday.net",                  "www.ettoday.net",          "ads?.ettoday.net"),
        ("ad2.ettoday.net",                  "ettoday.net",              "ads?\\d*.ettoday.net"),
        ("ads.ltn.com.tw",                   "www.ltn.com.tw",           "ads?.ltn.com.tw"),
        ("browser-intake-us3-datadoghq.com", "intake.datadoghq.com",    "browser-intake-*.datadoghq.com"),
        ("browser-intake-eu1-datadoghq.eu",  "datadoghq.eu",            "browser-intake-*.datadoghq.eu"),
        ("adunblock.workers.dev",            "workers.dev",              "adunblock*.workers.dev"),
        ("sub.adunblock99.workers.dev",      "adblock.workers.dev",     "subdomain adunblock*.workers.dev"),
    ]
    for block_host, allow_host, note in _REGEX_BLOCK_SAMPLES:
        cases.append(TestCase("Auto: Regex Domain Block", f"https://{block_host}/path", RES_BLOCK_403, f"正則封鎖: {note}"))
        cases.append(TestCase("Auto: Regex Domain Non-Match", f"https://{allow_host}/page", RES_ALLOW, f"非匹配放行: {note}"))

    for d in RULES_DB["PARAM_CLEANING_EXEMPTED_DOMAINS"]["EXACT"]:
        cases.append(TestCase("Auto: Param Exempt (Exact)", f"https://{d}/page?utm_source=test&fbclid=abc", RES_ALLOW, "參數淨化豁免域名，保留所有追蹤參數"))
    for d in RULES_DB["PARAM_CLEANING_EXEMPTED_DOMAINS"]["WILDCARDS"][:8]:
        cases.append(TestCase("Auto: Param Exempt (WC)", f"https://sub.{d}/api?gclid=test&device_id=abc", RES_ALLOW, "萬用字元參數淨化豁免域名"))

    for d in RULES_DB["SILENT_REWRITE_DOMAINS"]["WILDCARDS"]:
        cases.append(TestCase("Auto: Silent Rewrite Domain", f"https://www.{d}/page?utm_source=test", RES_REWRITE, "靜默重寫域名使用 REWRITE 而非 302 重定向"))

    # HEURISTIC regex: blocks ?ad_xxx=, ?ads_xxx=, ?campaign_xxx=, ?tracker_xxx= before param cleaning
    _heuristic_re = re.compile(r'[?&](ad|ads|campaign|tracker)_[a-z]+=', re.IGNORECASE)
    for prefix in RULES_DB["PARAMS_PREFIXES"]:
        sample_param = prefix.rstrip('_') + '_testval'
        test_path = f"/page?{sample_param}=test123"
        # Skip if the HEURISTIC regex or PATH_BLOCK would block before param cleaning runs
        if _heuristic_re.search(test_path): continue
        if is_path_keyword_blocked(test_path): continue
        cases.append(TestCase("Auto: Prefix Param Clean", f"https://example.com{test_path}", RES_CLEAN_302, f"前綴 '{prefix}' 觸發參數淨化"))

    for p in ['fb_ref', 'fb_source', 'from', 'ref', 'share_id']:
        cases.append(TestCase("Auto: Cosmetic Param Clean", f"https://example.com/page?{p}=test", RES_CLEAN_302, f"裝飾參數 '{p}' 應被淨化"))

    for p in ['code', 'id', 'p', 'page', 'product_id', 'q', 'query', 'search', 'session_id', 'state', 'token', 'format', 'lang', 'locale', 'salt', 's']:
        cases.append(TestCase("Auto: Param Whitelist Survive", f"https://example.com/page?{p}=value&utm_source=test", RES_CLEAN_302, f"白名單參數 '{p}' 應存活，utm_source 被移除觸發淨化"))

    static_test_exts = ['.css', '.js', '.jpg', '.png', '.gif', '.svg', '.woff2', '.mp4', '.pdf', '.json']
    for ext in static_test_exts:
        cases.append(TestCase("Edge: Static Ext Bypass", f"https://example.com/lib/affiliate/sponsor{ext}", RES_ALLOW, f"靜態副檔名 {ext} 豁免 PATH_BLOCK 關鍵字封鎖"))

    for prefix in ['/favicon', '/assets/', '/static/', '/images/', '/img/', '/js/', '/css/']:
        cases.append(TestCase("Edge: Exception Prefix Bypass", f"https://example.com{prefix}ad/sponsor.webp", RES_ALLOW, f"路徑前綴 '{prefix}' 豁免 HIGH_CONFIDENCE 掃描"))
    cases.append(TestCase("Edge: cdn-cgi Substring Bypass", "https://example.com/cdn-cgi/trace/ad/test", RES_ALLOW, "cdn-cgi 子串匹配豁免 HIGH_CONFIDENCE 掃描"))
    for seg in ['assets', 'static', 'images', 'img', 'css', 'js']:
        cases.append(TestCase("Edge: Segment Bypass", f"https://example.com/path/{seg}/ad/sponsor.webp", RES_ALLOW, f"路徑段 '/{seg}/' 豁免 HIGH_CONFIDENCE 掃描"))

    for domain, paths in RULES_DB["PATH_EXEMPTIONS"].items():
        for p in paths:
            test_url = f"https://{domain}{p if p.startswith('/') else '/' + p}?test=1"
            cases.append(TestCase("Auto: Path Exemption", test_url, RES_ALLOW, f"路徑豁免 {domain} 的 {p}"))

    cases.append(TestCase("Edge: Single Encoded /ad/", "https://example.com/%61%64/banner.webp", RES_BLOCK_403, "單次 URL 編碼 /ad/ 解碼後命中 HIGH_CONFIDENCE"))
    cases.append(TestCase("Edge: Mixed Case Path", "https://example.com/ADS/Banner/pixel.gif", RES_BLOCK_403, "路徑大小寫不敏感，/ADS/ 應命中 HIGH_CONFIDENCE"))
    cases.append(TestCase("Edge: Encoded Query Param", "https://example.com/page?utm%5Fsource=test", RES_ALLOW, "編碼的查詢參數鍵不觸發淨化 (原始鍵未匹配)"))
    cases.append(TestCase("Edge: Triple Nested Path", "https://example.com/a/b/c/d/e/f/ads/banner/pixel.gif", RES_BLOCK_403, "深層巢狀路徑中的 /ads/ 仍應被掃描到"))

    cases.append(TestCase("Edge: URL with Port", "https://example.com:8443/tracker/event", RES_BLOCK_403, "含端口號的 URL 正確解析 hostname 後命中關鍵字"))
    cases.append(TestCase("Edge: URL with Fragment", "https://example.com/page?utm_source=test#section", RES_CLEAN_302, "URL fragment 在淨化前被正確剝離"))
    cases.append(TestCase("Edge: Path Only Slash", "https://example.com/", RES_ALLOW, "根路徑無匹配，放行"))
    cases.append(TestCase("Edge: No Path", "https://example.com", RES_ALLOW, "無路徑 URL 正確解析為 / 放行"))
    cases.append(TestCase("Edge: Empty Query String", "https://example.com/page?", RES_ALLOW, "空查詢字串不觸發淨化"))
    cases.append(TestCase("Edge: Query Only Ampersand", "https://example.com/page?&", RES_ALLOW, "僅含 & 的查詢字串不崩潰"))
    cases.append(TestCase("Edge: Multiple Same Params", "https://example.com/page?utm_source=a&utm_source=b", RES_CLEAN_302, "重複參數全部被淨化"))
    cases.append(TestCase("Edge: Value-less Param", "https://example.com/page?utm_source", RES_CLEAN_302, "無值參數 (無等號) 仍應被淨化"))
    cases.append(TestCase("Edge: Very Long Path", f"https://example.com/{'a/' * 100}tracker/event", RES_BLOCK_403, "超長路徑仍能掃描到關鍵字"))

    cases.append(TestCase("Conflict: P0 vs Hard WL", "https://admob.com/page", RES_BLOCK_403, "PRIORITY_BLOCK 優先於任何白名單"))
    cases.append(TestCase("Conflict: Redirector vs Path", "https://adf.ly/safe/page.html", RES_BLOCK_403, "REDIRECTOR 判定優先於路徑安全豁免"))
    cases.append(TestCase("Conflict: Block Domain (No WL)", "https://sentry.io/api/data", RES_BLOCK_403, "sentry.io 在 BLOCK_DOMAINS + BLOCK_DOMAINS_WILDCARDS 中且不在 SOFT_WHITELIST，Step 6 直接封鎖"))
    cases.append(TestCase("Conflict: Hard WL + Keyword", "https://sendgrid.net/path/analytics/deep", RES_ALLOW, "HARD_WHITELIST 豁免 HIGH_CONFIDENCE 關鍵字掃描"))
    cases.append(TestCase("Conflict: Soft WL + Static", "https://cdn.shopify.com/files/campaign/image.jpg", RES_ALLOW, "SOFT_WHITELIST + 靜態副檔名雙重豁免"))
    cases.append(TestCase("Conflict: Critical Map vs Path Exempt", "https://www.youtube.com/ptracking", RES_BLOCK_403, "CRITICAL_PATH_MAP 在 PATH_EXEMPTIONS 之前執行"))
    cases.append(TestCase("Conflict: PRIORITY_DROP vs Static", "https://example.com/otel/v1/logs", RES_DROP_204, "PRIORITY_DROP 路徑匹配優先於靜態豁免"))
    cases.append(TestCase("Conflict: Param Exempt + Block Domain", "https://api.stripe.com/v1/charges?utm_source=test&device_id=abc", RES_ALLOW, "api.stripe.com 在參數淨化豁免域名中，且為 ABSOLUTE_BYPASS"))

    cases.append(TestCase("Mutation: Tracker with Typo", "https://example.com/trackerr/event", RES_BLOCK_403, "'trackerr' 包含 '/track' 子串，由 criticalPathScanner (Step 15) 無條件攔截"))
    cases.append(TestCase("Mutation: Ad with Extra Slash", "https://example.com//ad//banner.gif", RES_BLOCK_403, "雙斜線路徑中 /ad/ 仍命中 HIGH_CONFIDENCE"))
    cases.append(TestCase("Mutation: Analytics Substring", "https://example.com/user-analytics-dashboard", RES_BLOCK_403, "'analytics' 子串命中 PATH_BLOCK"))
    cases.append(TestCase("Mutation: Pixel in Filename", "https://example.com/image/pixel.gif", RES_BLOCK_403, "pixel.gif 命中 CRITICAL_PATH_GENERIC"))
    cases.append(TestCase("Mutation: Beacon as Endpoint", "https://example.com/api/beacon", RES_BLOCK_403, "/beacon 命中 CRITICAL_PATH_GENERIC"))
    cases.append(TestCase("Mutation: Collect with Query", "https://example.com/v1/collect?tid=UA-123", RES_BLOCK_403, "/v1/collect 命中 CRITICAL_PATH_GENERIC"))
    cases.append(TestCase("Mutation: Fingerprint Variant", "https://example.com/cdn/fingerprint/v3", RES_BLOCK_403, "/cdn/fingerprint/ 命中 CRITICAL_PATH_GENERIC"))
    cases.append(TestCase("Mutation: Canvas FP Path", "https://example.com/api/canvas-fingerprint/detect", RES_BLOCK_403, "canvas-fingerprint 命中 PATH_BLOCK"))
    cases.append(TestCase("Mutation: WebGL FP Path", "https://example.com/api/webgl-fp/hash", RES_BLOCK_403, "webgl-fp 命中 PATH_BLOCK"))
    cases.append(TestCase("Mutation: Audio FP Path", "https://example.com/api/audio-fingerprint/calc", RES_BLOCK_403, "audio-fingerprint 命中 PATH_BLOCK"))
    cases.append(TestCase("Mutation: Font Detect FP", "https://example.com/api/font-detect-fp/list", RES_BLOCK_403, "font-detect-fp 命中 PATH_BLOCK"))

    cases.append(TestCase("Regex: /ads/ path pattern", "https://example.com/v2/ads/campaign", RES_BLOCK_403, "HIGH_CONFIDENCE /ads/ (Step 14) 先於正則攔截"))
    cases.append(TestCase("Regex: /ad/ path pattern", "https://example.com/api/ad/load", RES_BLOCK_403, "HIGH_CONFIDENCE /ad/ (Step 14) 先於正則攔截"))
    cases.append(TestCase("Regex: /ads/ path with prefix", "https://example.com/v1/ads/load", RES_BLOCK_403, "HIGH_CONFIDENCE /ads/ (Step 14) 先於正則攔截"))
    cases.append(TestCase("Regex: tracker.gif file", "https://example.com/img/tracker.gif", RES_BLOCK_403, "criticalPathScanner (Step 15) 無條件命中 /track 子串"))
    cases.append(TestCase("Regex: Heuristic ad param", "https://example.com/page?ad_campaign=test", RES_BLOCK_403, "啟發式正則 [?&](ad|ads|campaign|tracker)_[a-z]+= (Step 17) 匹配 ad_campaign"))
    cases.append(TestCase("Regex: Heuristic tracker param", "https://example.com/page?tracker_id=test", RES_BLOCK_403, "啟發式正則 [?&](ad|ads|campaign|tracker)_[a-z]+= (Step 17) 匹配 tracker_id"))

    cases.append(TestCase("Edge: API Path Silent Rewrite", "https://example.com/api/v1/user?utm_source=test", RES_REWRITE, "/api/ 路徑觸發靜默重寫而非 302"))
    cases.append(TestCase("Edge: GraphQL Silent Rewrite", "https://example.com/graphql/query?fbclid=test", RES_REWRITE, "/graphql/ 路徑觸發靜默重寫"))
    cases.append(TestCase("Edge: REST Silent Rewrite", "https://example.com/rest/v2/data?gclid=test", RES_REWRITE, "/rest/ 路徑觸發靜默重寫"))
    cases.append(TestCase("Edge: JSON Suffix Rewrite", "https://example.com/data.json?utm_source=test", RES_REWRITE, ".json 後綴觸發靜默重寫"))
    cases.append(TestCase("Edge: api. Subdomain Rewrite", "https://api.example.com/data?utm_source=test", RES_REWRITE, "api. 開頭子域名觸發靜默重寫"))
    cases.append(TestCase("Edge: appapi. Subdomain Rewrite", "https://appapi.example.com/data?utm_source=test", RES_REWRITE, "appapi. 開頭子域名觸發靜默重寫"))

    for param in ['utm_test', 'utm_custom_field', 'ig_cb', 'ig_mid', 'asa_channel', 'tt_adid', 'li_sugr']:
        cases.append(TestCase("Auto: Regex Param Clean", f"https://example.com/page?{param}=value", RES_CLEAN_302, f"正則匹配參數 '{param}' 觸發淨化"))

    for k in RULES_DB["PRIORITY_DROP"]:
        cases.append(TestCase("Auto: Priority Drop Exact", f"https://unknown-site.com{k}", RES_DROP_204, f"PRIORITY_DROP 精確匹配 '{k}'"))

    cases.append(TestCase("Mutation: Coupang home-banner-ads", "https://cmapi.tw.coupang.com/home-banner-ads/v1", RES_BLOCK_403, "CRITICAL_PATH_MAP Step 4 精確封鎖 /home-banner-ads/"))
    cases.append(TestCase("Mutation: Coupang plp-ads", "https://cmapi.tw.coupang.com/plp-ads/v2/items", RES_BLOCK_403, "CRITICAL_PATH_MAP Step 4 精確封鎖 /plp-ads/"))
    cases.append(TestCase("Mutation: Coupang category-banner-ads", "https://cmapi.tw.coupang.com/category-banner-ads/v1", RES_BLOCK_403, "CRITICAL_PATH_MAP Step 4 精確封鎖 /category-banner-ads/"))
    cases.append(TestCase("Edge: Coupang vendor-items safe", "https://cmapi.tw.coupang.com/vendor-items/12345", RES_ALLOW, "Coupang 商品 API 不含 -ads/ 應放行"))

    cases.append(TestCase("Scoped: 104 v2 api device_id", "https://appapi.104.com.tw/v2/api/user?device_id=TEST", RES_ALLOW, "/v2/api/ 正向匹配 device_id 放行"))
    cases.append(TestCase("Scoped: 104 v2 api client_id", "https://appapi.104.com.tw/v2/api/user?client_id=TEST", RES_ALLOW, "/v2/api/ 白名單中無 client_id，但 client_id 不不在 PARAMS_GLOBAL 中，不觸發淨化"))
    cases.append(TestCase("Scoped: 104 api both params", "https://appapi.104.com.tw/api/login?device_id=A&client_id=B", RES_ALLOW, "/api/ 同時允許 device_id 和 client_id"))
    cases.append(TestCase("Scoped: 104 negative + positive overlap", "https://appapi.104.com.tw/2.0/ad/data?device_id=A&fbclid=B", RES_REWRITE, "!/2.0/ad/ 否決 device_id，fbclid 為全局追蹤參數，兩者皆被剝離"))
    cases.append(TestCase("Scoped: Subdomain inheritance", "https://sub.104.com.tw/api/data?device_id=TEST", RES_ALLOW, "子域名繼承 104.com.tw SCOPED 規則，/api/ device_id 放行"))

    cases.append(TestCase("Security: HMAC sig bypass", "https://example.com/webhook?utm_source=test&sig=abcdef123", RES_ALLOW, "signature/sig/hmac 參數存在時停止淨化保護簽章"))
    cases.append(TestCase("Security: HMAC hmac bypass", "https://example.com/callback?fbclid=test&hmac=sha256hash", RES_ALLOW, "hmac 參數存在時停止淨化"))
    cases.append(TestCase("Security: HMAC signature bypass", "https://example.com/verify?gclid=test&signature=rsa2048", RES_ALLOW, "signature 參數存在時停止淨化"))

    cases.append(TestCase("Mix: Clean only tracking", "https://example.com/page?q=search&utm_source=google&page=2", RES_CLEAN_302, "僅移除 utm_source，保留 q 和 page"))
    cases.append(TestCase("Mix: All params whitelisted", "https://example.com/page?q=test&page=1&lang=en", RES_ALLOW, "所有參數均在白名單中，無淨化觸發"))
    cases.append(TestCase("Mix: All params tracked", "https://example.com/page?utm_source=a&fbclid=b&gclid=c", RES_CLEAN_302, "所有參數均為追蹤參數，全部移除"))
    cases.append(TestCase("Mix: Prefix + Global combo", "https://example.com/page?_ga=1.234&utm_medium=cpc&q=test", RES_CLEAN_302, "前綴與全局規則同時命中，白名單參數存活"))

    cases.append(TestCase("Edge: CheckConnection case insensitive", "https://example.com/accounts/checkconnection", RES_DROP_204, "CheckConnection 路徑大小寫不敏感，觸發 204"))
    cases.append(TestCase("Edge: CheckConnection with query", "https://example.com/accounts/CheckConnection?t=123", RES_DROP_204, "CheckConnection 含查詢參數仍觸發 204"))
    cases.append(TestCase("Edge: CheckConnection deep path", "https://random-site.org/v2/accounts/checkconnection/status", RES_DROP_204, "CheckConnection 在任意深度路徑中均觸發 204"))

    cases.append(TestCase("Conflict: Soft WL + Static Keyword", f"https://{dynamic_soft_wl}/lib/affiliate.min.js", RES_ALLOW, "軟白名單 + .js 靜態副檔名雙重豁免 PATH_BLOCK 關鍵字掃描"))
    cases.append(TestCase("Conflict: Soft WL + Non-Static Keyword", f"https://{dynamic_soft_wl}/path/affiliate/event", RES_BLOCK_403, "軟白名單但非靜態路徑，PATH_BLOCK 關鍵字掃描仍生效"))

    cases.append(TestCase("Edge: DROP keyword in static file", "https://example.com/lib/heartbeat.min.css", RES_ALLOW, "靜態副檔名 .css 豁免 DROP 關鍵字 'heartbeat' 掃描"))
    cases.append(TestCase("Edge: DROP keyword in /js/ prefix", "https://example.com/js/live-log.config.json", RES_ALLOW, "/js/ 前綴 + .json 靜態副檔名豁免 DROP 掃描"))

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
                return False, RES_BLOCK_403, str(body)
            if code == 204:
                if expected_type == RES_DROP_204: return True, RES_DROP_204, ""
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

# ==========================================
#  INCREMENTAL NODE.JS TEST CACHE HELPERS
# ==========================================

def _compute_node_cache_key() -> str:
    """Compute a 16-char MD5 fingerprint of VERSION + RULES_DB.
    Any rule edit or version bump produces a different key, invalidating the cache."""
    raw = VERSION + json.dumps(RULES_DB, sort_keys=True, ensure_ascii=False)
    return hashlib.md5(raw.encode("utf-8")).hexdigest()[:16]

def _node_cache_path(key: str) -> Path:
    return Path(f"_node_cache_{key}.json")

def _load_node_cache(key: str) -> Optional[List[dict]]:
    """Return cached Node.js results list if a valid cache file exists, else None."""
    p = _node_cache_path(key)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return None

def _save_node_cache(key: str, results: List[dict]) -> None:
    """Persist Node.js results and purge any stale cache files from previous builds."""
    for old in Path(".").glob("_node_cache_*.json"):
        try:
            old.unlink()
        except Exception:
            pass
    _node_cache_path(key).write_text(json.dumps(results), encoding="utf-8")

def run_tests():
    print(f"1. [SSOT COMPILER] Compiling Python RULES_DB to Dual-Target JavaScript (V{VERSION} · {RELEASE_DATE})")
    print(f"   📦 Rules Stats: "
          f"domains={RULES_STATS['block_domains']} | "
          f"critical={RULES_STATS['critical_paths']} | "
          f"path_kw={RULES_STATS['path_keywords']} | "
          f"drop_kw={RULES_STATS['drop_keywords']} | "
          f"params={RULES_STATS['param_rules']} | "
          f"whitelist={RULES_STATS['whitelist']} | "
          f"TOTAL={TOTAL_RULE_COUNT}")
    js_surge_content = compile_surge()
    js_tampermonkey_content = compile_tampermonkey()
    js_surge_filename = "URL-Ultimate-Filter-Surge.js"
    js_tm_filename = "URL-Ultimate-Filter-Tampermonkey.user.js"

    cases = generate_full_coverage_cases()
    unique_cases = {c.category + c.url + c.expected: c for c in cases}.values()
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

    _cache_key = _compute_node_cache_key()
    _cached = _load_node_cache(_cache_key)

    if _cached is not None:
        print(f"2. [BATCH ENGINE] Cache HIT ({_cache_key}) — skipping Node.js ({len(final_cases)} cases loaded from cache).")
        results = _cached
    else:
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
            try:
                stdout, stderr = p.communicate(timeout=120)
            except Exception:
                p.kill()
                p.communicate()
                print("[FATAL ERROR] Node.js runner timed out after 120s — process killed.")
                sys.exit(1)

            if p.returncode != 0:
                print(f"[FATAL ERROR] Node Execution Failed:\n{stderr}")
                sys.exit(1)

            results = json.loads(stdout)
            _save_node_cache(_cache_key, results)
        finally:
            Path(runner_path).unlink(missing_ok=True)
            Path(payload_path).unlink(missing_ok=True)

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
        # 測試通過後，將實際測試案例數回填至 SCRIPT_BUILD 常數
        js_surge_content = js_surge_content.replace('__SSOT_TEST_COUNT__', str(total))
        js_tampermonkey_content = js_tampermonkey_content.replace('__SSOT_TEST_COUNT__', str(total))
        with open(js_surge_filename, "w", encoding="utf-8") as f: f.write(js_surge_content)
        with open(js_tm_filename, "w", encoding="utf-8") as f: f.write(js_tampermonkey_content)

        # Generate Surge REJECT-DROP rule list (DNS-level blocking)
        surge_reject_filename = "URL-Ultimate-Filter-Surge-REJECT.list"
        surge_reject_content = compile_surge_reject_list()
        with open(surge_reject_filename, "w", encoding="utf-8") as f: f.write(surge_reject_content)
        reject_rule_count = sum(1 for l in surge_reject_content.splitlines() if l.startswith("DOMAIN"))

        update_changelog()

        print(f"\n✅  SSOT DUAL-TARGET BUILD & TEST PASSED")
        print(f"📄  Surge Edition Saved: {js_surge_filename}")
        print(f"📄  Tampermonkey Edition Saved: {js_tm_filename}")
        print(f"📄  Surge REJECT List Saved: {surge_reject_filename} ({reject_rule_count} rules)")
        print(f"📄  Test Report Saved for Pages: {report_name}")
    else:
        print(f"\n❌  SSOT TEST FAILED")
        print(f"⚠️  JavaScript Generation SKIPPED due to test failures.")
    print("="*55 + "\n")

if __name__ == "__main__":
    run_tests()
