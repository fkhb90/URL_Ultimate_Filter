// ==UserScript==
// @name         URL Ultimate Filter V45.20
// @namespace    http://tampermonkey.net/
// @version      45.20
// @date         2026-04-06
// @description  SSOT 前端防護盾牌 V45.20 (2026-04-06) | 1340 rules — 極簡盾牌 UI，獨立計數器，點擊外部自動收合。
// @rules        1340 total (275 domains · 280 critical · 109 param)
// @author       Jerry
// @match        *://*/*
// @run-at       document-start
// @grant        GM_registerMenuCommand
// ==/UserScript==

(function() {
    'use strict';
/**
 * @file    URL-Ultimate-Filter-Tampermonkey.js
 * @version 45.20
 * @date    2026-04-06
 * @rules   1340 total (275 domains, 280 critical paths, 403 path keywords, 109 param rules)
 * @build   SSOT Compiler — Dual-Target Compilation
 */

const CONFIG = { DEBUG_MODE: false, AC_SCAN_MAX_LENGTH: 600 };
const SCRIPT_VERSION = '45.20';
const SCRIPT_BUILD = 'V45.20 (2026-04-06) | 1340 rules | 2527 tests';
const EMPTY_SET = new Set();

const OAUTH_SAFE_HARBOR = {
    DOMAINS: new Set([
    'accounts.google.com', 'accounts.google.com.tw', 'accounts.youtube.com', 'appleid.apple.com', 'idmsa.apple.com', 'facebook.com',
    'www.facebook.com', 'm.facebook.com', 'login.microsoftonline.com', 'login.live.com', 'github.com', 'api.twitter.com',
    'api.x.com'
  ]),
    PATHS_REGEX: [ /\/(login|oauth|oauth2|authorize|signin|session)(\/|\?|$)/i ]
};

const PARAM_CLEANING_EXEMPTED_DOMAINS = {
    EXACT: new Set([
    'shopback.com.tw', 'extrabux.com', 'buy.line.me'
  ]),
    WILDCARDS: new Set([
    'feedly.com', 'shopee.tw', 's3.amazonaws.com', 'storage.googleapis.com', 'core.windows.net', 'api.line.me',
    'api.newebpay.com', 'api.tappayapis.com', 'api.stripe.com', 'api.github.com', 'api.twitch.tv', 'cdn.discordapp.com',
    'slack.com', 'cloudfunctions.net'
  ])
};

const SILENT_REWRITE_DOMAINS = {
    EXACT: new Set([]),
    WILDCARDS: new Set([
    '591.com.tw', '104.com.tw'
  ])
};

const ABSOLUTE_BYPASS_DOMAINS = {
    EXACT: new Set([
    'api.ecpay.com.tw', 'payment.ecpay.com.tw', 'api.map.ecpay.com.tw', 'api.jkos.com'
  ]),
    WILDCARDS: new Set([
    'cathaybk.com.tw', 'ctbcbank.com', 'esunbank.com.tw', 'fubon.com', 'taishinbank.com.tw', 'richart.tw',
    'bot.com.tw', 'cathaysec.com.tw', 'chb.com.tw', 'citibank.com.tw', 'dawho.tw', 'dbs.com.tw',
    'firstbank.com.tw', 'hncb.com.tw', 'hsbc.co.uk', 'hsbc.com.tw', 'landbank.com.tw', 'megabank.com.tw',
    'scsb.com.tw', 'sinopac.com', 'sinotrade.com.tw', 'standardchartered.com.tw', 'tcb-bank.com.tw', 'paypal.com',
    'stripe.com', 'taiwanpay.com.tw', 'twca.com.tw', 'twmp.com.tw', 'pay.taipei', 'momopay.com.tw',
    'mymobibank.com.tw', 'post.gov.tw', 'nhi.gov.tw', 'mohw.gov.tw', 'tdcc.com.tw'
  ])
};

const RULES = {
  PRIORITY_BLOCK_DOMAINS: new Set([
    'cdn-path.com', 'doorphone92.com', 'easytomessage.com', 'penphone92.com', 'sir90hl.com', 'uymgg1.com',
    'admob.com', 'ads.google.com', 'adservice.google.com', 'adservice.google.com.tw', 'doubleclick.net', 'googleadservices.com',
    'googlesyndication.com', 'crashlyticsreports-pa.googleapis.com', 'firebaselogging-pa.googleapis.com', 'imasdk.googleapis.com', 'measurement.adservices.google.com', 'privacysandbox.googleapis.com',
    'business.facebook.com', 'connect.facebook.net', 'graph.facebook.com', '2o7.net', 'adobedc.net', 'demdex.net',
    'everesttech.net', 'omtrdc.net', '3lift.com', 'adnxs.com', 'advertising.com', 'amazon-adsystem.com',
    'bidswitch.net', 'indexexchange.com', 'media.net', 'sharethrough.com', 'teads.tv', 'crwdcntrl.net',
    'exelator.com', 'eyeota.com', 'krxd.net', 'lotame.com', 'liadm.com', 'rlcdn.com',
    'tapad.com', 'contextweb.com', 'mathtag.com', 'rfihub.com', 'adcolony.com', 'applovin.com',
    'chartboost.com', 'ironsrc.com', 'pangle.io', 'popads.net', 'tapjoy.com', 'unityads.unity3d.com',
    'vungle.com', 'outbrain.com', 'taboola.com', 'app-measurement.com', 'branch.io', 'singular.net',
    'ad.etmall.com.tw', 'ad.line.me', 'ad-history.line.me', 'ads.linkedin.com', 'ads.tiktok.com', 'analytics.tiktok.com',
    'cdn.segment.com', 'clarity.ms', 'fullstory.com', 'inmobi.com', 'inner-active.mobi', 'launchdarkly.com',
    'split.io', 'iadsdk.apple.com', 'metrics.icloud.com', 'ad.impactify.io', 'impactify.media', 'adsv.omgrmn.tw',
    'browser.sentry-cdn.com', 'caid.china-caa.org', 'events.tiktok.com', 'ibytedtos.com', 'log.tiktokv.com', 'log16-normal-c-useast1a.tiktokv.com',
    'mon.tiktokv.com', 'mon-va.tiktokv.com', 'analysis.shein.com', 'dc.shein.com', 'st.shein.com', 'report.temu.com',
    'alimama.com', 'hm.baidu.com', 'mmstat.com', 'pos.baidu.com', 'sm.cn', 'sofire.baidu.com',
    'sp0.baidu.com', 'sp1.baidu.com', 'tanx.com', 'uc.cn', 'ucweb.com', 'uczzd.cn',
    'ynuf.alipay.com', 'cms-statistics.quark.cn', 'stat.quark.cn', 'unpm-upaas.quark.cn', 'browser.360.cn', 's.360.cn',
    'shouji.360.cn', 'stat.360.cn', 'inte.sogou.com', 'lu.sogou.com', 'pb.sogou.com', 'ping.sogou.com',
    'analytics.shopee.tw', 'apm.tracking.shopee.tw', 'dem.shopee.com', 'dmp.shopee.tw', 'live-apm.shopee.tw', 'log-collector.shopee.tw',
    'analysis.momoshop.com.tw', 'ecdmp.momoshop.com.tw', 'event.momoshop.com.tw', 'log.momoshop.com.tw', 'pixel.momoshop.com.tw', 'rtb.momoshop.com.tw',
    'sspap.momoshop.com.tw', 'trace.momoshop.com.tw', 'trk.momoshop.com.tw', 'jslog.coupang.com', 'mercury.coupang.com', 'ad.gamer.com.tw',
    'ad-geek.net', 'ad-hub.net', 'ad-serv.teepr.com', 'ad-tracking.dcard.tw', 'analysis.tw', 'appier.net',
    'b.bridgewell.com', 'cacafly.com', 'clickforce.com.tw', 'fast-trk.com', 'funp.com', 'guoshipartners.com',
    'imedia.com.tw', 'is-tracking.com', 'itad.linetv.tw', 'likr.tw', 'scupio.com', 'sitetag.us',
    'tagtoo.co', 'tenmax.io', 'trk.tw', 'urad.com.tw', 'vpon.com', 'adnext-a.akamaihd.net',
    'toots-a.akamaihd.net', 'analytics.twitter.com', 'edge-analytics.amazonaws.com', 'edge-tracking.cloudflare.com', 'insight.linkedin.com', 'px.ads.linkedin.com'
  ]),
  REDIRECTOR_HOSTS: new Set([
    'adf.ly', 'ay.gy', 'gloyah.net', 'j.gs', 'q.gs', 'zo.ee',
    'direct-link.net', 'file-link.net', 'filemedia.net', 'link-center.net', 'link-hub.net', 'link-target.net',
    'link-to.net', 'linkvertise.com', 'linkvertise.download', 'up-to-down.net', 'links-loot.com', 'linksloot.net',
    'loot-link.com', 'loot-links.com', 'lootdest.com', 'lootdest.info', 'lootdest.org', 'lootlabs.gg',
    'lootlink.org', 'lootlinks.co', 'boost.ink', 'booo.st', 'bst.gg', 'bst.wtf',
    'letsboost.net', 'mboost.me', 'rekonise.com', 'sub2get.com', 'sub2unlock.com', 'sub4unlock.io',
    'subfinal.com', 'filecrypt.cc', 'filecrypt.co', 'keeplinks.org', 'lockr.so', 'adpaylink.com',
    'adshrink.com', 'adyou.me', 'clicksfly.com', 'cutwin.com', 'cuty.io', 'droplink.co',
    'exe.io', 'linkpays.in', 'paster.so', 'pubiza.com', 'safelinku.com', 'shorte.st',
    'shortzon.com', 'shrink.pe', 'shrinkearn.com', 'shrinkme.io', 'shrtfly.com', 'smoner.com',
    'try2link.com', 'uii.io', 'v2links.com', 'work.ink', 'za.gl', '1ink.cc',
    'adfoc.us', 'adsafelink.com', 'adshnk.com', 'adz7short.space', 'aylink.co', 'bc.vc',
    'bcvc.ink', 'birdurls.com', 'ceesty.com', 'clik.pw', 'clk.sh', 'cpmlink.net',
    'cpmlink.pro', 'cutpaid.com', 'dlink3.com', 'dz4link.com', 'earnlink.io', 'exe-links.com',
    'exeo.app', 'fc-lc.com', 'fir3.net', 'gestyy.com', 'gitlink.pro', 'gplinks.co',
    'hotshorturl.com', 'icutlink.com', 'kimochi.info', 'kingofshrink.com', 'linegee.net', 'link1s.com',
    'linkmoni.com', 'linkpoi.me', 'linkshrink.net', 'linksly.co', 'lnk2.cc', 'mangalist.org',
    'megalink.pro', 'met.bz', 'oke.io', 'oko.sh', 'oni.vn', 'onlinefreecourse.net',
    'ouo.io', 'ouo.press', 'pahe.plus', 'payskip.org', 'pingit.im', 'shortlinkto.biz',
    'shortmoz.link', 'shrt10.com', 'similarsites.com', 'smilinglinks.com', 'spacetica.com', 'spaste.com',
    'stfly.me', 'stfly.xyz', 'supercheats.com', 'techgeek.digital', 'techstudify.com', 'techtrendmakers.com',
    'thinfi.com', 'tnshort.net', 'tribuntekno.com', 'turdown.com', 'tutwuri.id', 'urlcash.com',
    'urlcash.org', 'vinaurl.net', 'vzturl.com', 'xpshort.com', 'zegtrends.com'
  ]),
  REDIRECT_EXTRACT_HOSTS: new Set([
    'go.skimresources.com'
  ]),

  HARD_WHITELIST: {
    EXACT: new Set([
    'iappapi.investing.com', 'cdn.oaistatic.com', 'files.oaiusercontent.com', 'claude.ai', 'gemini.google.com', 'perplexity.ai',
    'www.perplexity.ai', 'pplx-next-static-public.perplexity.ai', 'private-us-east-1.monica.im', 'api.felo.ai', 'qianwen.aliyun.com', 'static.stepfun.com',
    'api.openai.com', 'a-api.anthropic.com', 'api.feedly.com', 'sandbox.feedly.com', 'cloud.feedly.com', 'translate.google.com',
    'translate.googleapis.com', 'inbox.google.com', 'reportaproblem.apple.com', 'sso.godaddy.com', 'api.login.yahoo.com', 'firebaseappcheck.googleapis.com',
    'firebaseinstallations.googleapis.com', 'firebaseremoteconfig.googleapis.com', 'accounts.felo.me', 'api.etmall.com.tw', 'tw.fd-api.com', 'tw.mapi.shp.yahoo.com',
    'code.createjs.com', 'raw.githubusercontent.com', 'userscripts.adtidy.org', 'api.github.com', 'api.vercel.com', 'gateway.facebook.com',
    'graph.instagram.com', 'graph.threads.net', 'i.instagram.com', 'api.discord.com', 'api.twitch.tv', 'api.line.me',
    'today.line.me', 'pro.104.com.tw', 'appapi.104.com.tw', 'datadog.pool.ntp.org', 'ewp.uber.com', 'copilot.microsoft.com',
    'firebasedynamiclinks.googleapis.com', 'obs-tw.line-apps.com', 'obs.line-scdn.net'
  ]),
    WILDCARDS: new Set([
    'sendgrid.net', 'agirls.aotter.net', 'query1.finance.yahoo.com', 'query2.finance.yahoo.com', 'mitake.com.tw', 'money-link.com.tw',
    '591.com.tw', '104.com.tw', 'icloud.com', 'apple.com', 'whatsapp.net', 'update.microsoft.com',
    'windowsupdate.com', 'atlassian.net', 'auth0.com', 'okta.com', 'nextdns.io', 'archive.is',
    'archive.li', 'archive.ph', 'archive.today', 'archive.vn', 'cc.bingj.com', 'perma.cc',
    'timetravel.mementoweb.org', 'web-static.archive.org', 'web.archive.org', 'googlevideo.com', 'app.goo.gl', 'goo.gl',
    'browserleaks.com'
  ])
  },

  SOFT_WHITELIST: {
    EXACT: new Set([
    'gateway.shopback.com.tw', 'api.anthropic.com', 'api.cohere.ai', 'api.digitalocean.com', 'api.fastly.com', 'api.heroku.com',
    'api.hubapi.com', 'api.mailgun.com', 'api.netlify.com', 'api.pagerduty.com', 'api.sendgrid.com', 'api.telegram.org',
    'api.zendesk.com', 'duckduckgo.com', 'legy.line-apps.com', 'secure.gravatar.com', 'api.asana.com', 'api.dropboxapi.com',
    'api.figma.com', 'api.notion.com', 'api.trello.com', 'api.cloudflare.com', 'auth.docker.io', 'database.windows.net',
    'login.docker.com', 'api.irentcar.com.tw', 'usiot.roborock.com', 'prism.ec.yahoo.com', 'graphql.ec.yahoo.com', 'visuals.feedly.com',
    'api.revenuecat.com', 'api-paywalls.revenuecat.com', 'account.uber.com', 'xlb.uber.com', 'cmapi.tw.coupang.com', 'api.ipify.org',
    'gcp-data-api.ltn.com.tw', 's.pinimg.com', 'cdn.shopify.com'
  ]),
    WILDCARDS: new Set([
    'chatgpt.com', 'shopee.com', 'shopeemobile.com', 'shopee.io', 'youtube.com', 'facebook.com',
    'instagram.com', 'twitter.com', 'tiktok.com', 'spotify.com', 'netflix.com', 'disney.com',
    'linkedin.com', 'discord.com', 'googleapis.com', 'book.com.tw', 'citiesocial.com', 'coupang.com',
    'iherb.biz', 'iherb.com', 'm.youtube.com', 'momo.dm', 'momoshop.com.tw', 'pxmart.com.tw',
    'pxpayplus.com', 'shopback.com.tw', 'akamaihd.net', 'amazonaws.com', 'cloudflare.com', 'cloudfront.net',
    'fastly.net', 'fbcdn.net', 'gstatic.com', 'jsdelivr.net', 'cdnjs.cloudflare.com', 'twimg.com',
    'unpkg.com', 'ytimg.com', 'new-reporter.com', 'wp.com', 'flipboard.com', 'inoreader.com',
    'itofoo.com', 'newsblur.com', 'theoldreader.com', 'azurewebsites.net', 'cloudfunctions.net', 'digitaloceanspaces.com',
    'github.io', 'gitlab.io', 'netlify.app', 'oraclecloud.com', 'pages.dev', 'vercel.app',
    'windows.net', 'threads.net', 'threads.com', 'slack.com', 'feedly.com', 'ak.sv',
    'bayimg.com', 'beeimg.com', 'binbox.io', 'casimages.com', 'cocoleech.com', 'cubeupload.com',
    'dlupload.com', 'fastpic.org', 'fotosik.pl', 'gofile.download', 'ibb.co', 'imagebam.com',
    'imageban.ru', 'imageshack.com', 'imagetwist.com', 'imagevenue.com', 'imgbb.com', 'imgbox.com',
    'imgflip.com', 'imx.to', 'indishare.org', 'infidrive.net', 'k2s.cc', 'katfile.com',
    'mirrored.to', 'multiup.io', 'nmac.to', 'noelshack.com', 'pic-upload.de', 'pixhost.to',
    'postimg.cc', 'prnt.sc', 'sfile.mobi', 'thefileslocker.net', 'turboimagehost.com', 'uploadhaven.com',
    'uploadrar.com', 'usersdrive.com', '__sbcdn'
  ])
  },

  BLOCK_DOMAINS: new Set([
    'anymind360.com', 'vt.quark.cn', 'iqr.chinatimes.com', 'ecount.ctee.com.tw', 'sdk.gamania.dev', 'udc.yahoo.com',
    'csc.yahoo.com', 'beap.gemini.yahoo.com', 'opus.analytics.yahoo.com', 'noa.yahoo.com', 'sspap.pchome.tw', 'rtb.pchome.tw',
    'log.pchome.com.tw', 'ad.pchome.com.tw', 'vm5apis.com', 'vlitag.com', 'intentarget.com', 'innity.net',
    'ad-specs.guoshippartners.com', 'cdn.ad.plus', 'cdn.doublemax.net', 'udmserve.net', 'signal-snacks.gliastudios.com', 'adc.tamedia.com.tw',
    'log.zoom.us', 'metrics.uber.com', 'event-tracker.uber.com', 'cn-geo1.uber.com', 'udp.yahoo.com', 'analytics.yahoo.com',
    'effirst.com', 'px.effirst.com', 'simonsignal.com', 'analytics.etmall.com.tw', 'bam.nr-data.net', 'bam-cell.nr-data.net',
    'lrkt-in.com', 'cdn.lr-ingest.com', 'r.lr-ingest.io', 'api-iam.intercom.io', 'openfpcdn.io', 'fingerprintjs.com',
    'fundingchoicesmessages.google.com', 'hotjar.com', 'segment.io', 'mixpanel.com', 'amplitude.com', 'crazyegg.com',
    'bugsnag.com', 'sentry.io', 'newrelic.com', 'logrocket.com', 'fpjs.io', 'adunblock1.static-cloudflare.workers.dev',
    'guce.oath.com', 'app-site-association.cdn-apple.com', 'cdn-edge-tracking.com', 'edge-telemetry.akamai.com', 'edgecompute-analytics.com', 'monitoring.edge-compute.io',
    'realtime-edge.fastly.com', 'log.felo.ai', 'event.sc.gearupportal.com', 'pidetupop.com', 'adform.net', 'adsrvr.org',
    'analytics.line.me', 'analytics.slashdotmedia.com', 'analytics.strava.com', 'api.pendo.io', 'c.clarity.ms', 'c.segment.com',
    'chartbeat.com', 'clicktale.net', 'clicky.com', 'comscore.com', 'customer.io', 'data.investing.com',
    'datadoghq.com', 'dynatrace.com', 'fullstory.com', 'heap.io', 'inspectlet.com', 'iterable.com',
    'keen.io', 'kissmetrics.com', 'loggly.com', 'matomo.cloud', 'mgid.com', 'mouseflow.com',
    'mparticle.com', 'mlytics.com', 'nr-data.net', 'oceanengine.com', 'openx.net', 'optimizely.com',
    'piwik.pro', 'posthog.com', 'quantserve.com', 'revcontent.com', 'rudderstack.com', 'segment.com',
    'semasio.net', 'snowplowanalytics.com', 'statcounter.com', 'statsig.com', 'static.ads-twitter.com', 'sumo.com',
    'sumome.com', 'tealium.com', 'track.hubspot.com', 'track.tiara.daum.net', 'track.tiara.kakao.com', 'vwo.com',
    'yieldlab.net', 'fingerprint.com', 'doubleverify.com', 'iasds.com', 'moat.com', 'moatads.com',
    'sdk.iad-07.braze.com', 'serving-sys.com', 'tw.ad.doubleverify.com', 'agkn.com', 'id5-sync.com', 'liveramp.com',
    'permutive.com', 'tags.tiqcdn.com', 'klaviyo.com', 'marketo.com', 'mktoresp.com', 'pardot.com',
    'instana.io', 'launchdarkly.com', 'raygun.io', 'navify.com', 'cnzz.com', 'umeng.com',
    'talkingdata.com', 'jiguang.cn', 'getui.com', 'mdap.alipay.com', 'loggw-ex.alipay.com', 'pgdt.gtimg.cn',
    'afd.baidu.com', 'als.baidu.com', 'cpro.baidu.com', 'dlswbr.baidu.com', 'duclick.baidu.com', 'feed.baidu.com',
    'h2tcbox.baidu.com', 'hm.baidu.com', 'hmma.baidu.com', 'mobads-logs.baidu.com', 'mobads.baidu.com', 'nadvideo2.baidu.com',
    'nsclick.baidu.com', 'sp1.baidu.com', 'voice.baidu.com', '3gimg.qq.com', 'fusion.qq.com', 'ios.bugly.qq.com',
    'lives.l.qq.com', 'monitor.uu.qq.com', 'pingma.qq.com', 'sdk.e.qq.com', 'wup.imtt.qq.com', 'appcloud.zhihu.com',
    'appcloud2.in.zhihu.com', 'crash2.zhihu.com', 'mqtt.zhihu.com', 'sugar.zhihu.com', 'agn.aty.sohu.com', 'apm.gotokeep.com',
    'cn-huabei-1-lg.xf-yun.com', 'gs.getui.com', 'log.b612kaji.com', 'pc-mon.snssdk.com', 'sensorsdata.cn', 'stat.m.jd.com',
    'trackapp.guahao.cn', 'traffic.mogujie.com', 'wmlog.meituan.com', 'zgsdk.zhugeio.com', 'admaster.com.cn', 'adview.cn',
    'alimama.com', 'getui.net', 'gepush.com', 'gridsum.com', 'growingio.com', 'igexin.com',
    'jpush.cn', 'kuaishou.com', 'miaozhen.com', 'mmstat.com', 'pangolin-sdk-toutiao.com', 'talkingdata.cn',
    'tanx.com', 'umeng.cn', 'umeng.co', 'umengcloud.com', 'youmi.net', 'zhugeio.com',
    'appnext.hs.llnwd.net', 'fusioncdn.com', 'abema-adx.ameba.jp', 'ad.12306.cn', 'ad.360in.com', 'adroll.com',
    'ads.yahoo.com', 'adserver.yahoo.com', 'appnexus.com', 'bluekai.com', 'casalemedia.com', 'doubleclick.net',
    'googleadservices.com', 'googlesyndication.com', 'outbrain.com', 'taboola.com', 'rubiconproject.com', 'pubmatic.com',
    'openx.com', 'smartadserver.com', 'spotx.tv', 'yandex.ru', 'addthis.com', 'onesignal.com',
    'sharethis.com', 'bat.bing.com', 'clarity.ms', 'elads.kocpc.com.tw', 'eservice.emarsys.net', 'at-display-as.deliveryhero.io',
    'stun.services.mozilla1.com'
  ]),
  BLOCK_DOMAINS_WILDCARDS: new Set([
    'sentry.io', 'pidetupop.com', 'cdn-net.com', 'lr-ingest.io', 'aotter.net', 'ssp.yahoo.com',
    'pbs.yahoo.com', 'ay.delivery', 'cootlogix.com', 'ottadvisors.com', 'newaddiscover.com', 'app-ads-services.com',
    'app-measurement.com', 'adjust.com', 'adjust.net', 'appsflyer.com', 'onelink.me', 'branch.io',
    'app.link', 'kochava.com', 'scorecardresearch.com', 'rayjump.com', 'mintegral.net', 'tiktokv.com',
    'byteoversea.com', 'criteo.com', 'criteo.net', 'adservices.google.com', 'ad2n.com', 'vpon.com',
    'tenmax.io', 'clickforce.com.tw', 'onead.com.tw', 'bridgewell.com', 'tagtoo.co', 'scupio.com',
    'adbottw.net'
  ]),

  BLOCK_DOMAINS_REGEX: [
    /^ads?\d*\.(?:ettoday\.net|ltn\.com\.tw)$/i, /^browser-intake-[\w.-]*datadoghq\.(?:com|eu|us)$/i, /(?:^|\.)adunblock\d*.*\.workers\.dev$/i
  ],

  CRITICAL_PATH: {
    MAP: new Map([
    ['statsig.anthropic.com', new Set([
        'DROP:/v1/rgstr'
      ])],
    ['logx.optimizely.com', new Set([
        'DROP:/v1/events'
      ])],
    ['cpdl-deferrer.91app.com', new Set([
        'DROP:deferrer-log'
      ])],
    ['siftscience.com', new Set([
        'DROP:/v3/accounts/', 'DROP:/mobile_events'
      ])],
    ['o.alicdn.com', new Set([
        '/tongyi-fe/lib/cnzz/c.js', '/tongyi-fe/lib/cnzz/z.js'
      ])],
    ['qwen-api.zaodian.com', new Set([
        '/api/app/template/v1/feed'
      ])],
    ['file.chinatimes.com', new Set([
        '/ad-param.json'
      ])],
    ['health.tvbs.com.tw', new Set([
        '/health-frontend-js/ad-read-page.js'
      ])],
    ['static.ctee.com.tw', new Set([
        '/js/ad2019.min.js', '/js/third-party-sticky-ad-callback.min.js'
      ])],
    ['www.youtube.com', new Set([
        '/ptracking', '/api/stats/atr', '/api/stats/qoe', '/api/stats/playback',
        '/youtubei/v1/log_event', '/youtubei/v1/log_interaction'
      ])],
    ['m.youtube.com', new Set([
        '/ptracking', '/api/stats/atr', '/api/stats/qoe', '/api/stats/playback',
        '/youtubei/v1/log_event', '/youtubei/v1/log_interaction'
      ])],
    ['youtubei.googleapis.com', new Set([
        '/youtubei/v1/log_event', '/youtubei/v1/log_interaction', '/api/stats/', '/youtubei/v1/notification/record_interactions'
      ])],
    ['googlevideo.com', new Set([
        '/ptracking', '/videoplayback?ptracking='
      ])],
    ['api.uber.com', new Set([
        '/ramen/v1/events', '/v3/mobile-event', '/advertising/v1/', '/eats/advertising/',
        '/rt/users/v1/device-info'
      ])],
    ['api.ubereats.com', new Set([
        '/v1/eats/advertising', '/ramen/v1/events'
      ])],
    ['cn-geo1.uber.com', new Set([
        '/ramen/v1/events', '/v3/mobile-event', '/monitor/v2/logs'
      ])],
    ['tw.mapi.shp.yahoo.com', new Set([
        '/w/analytics', '/v1/instrumentation', '/ws/search/tracking', '/dw/tracker'
      ])],
    ['tw.buy.yahoo.com', new Set([
        '/b/ss/', '/ws/search/tracking', '/activity/record'
      ])],
    ['unwire.hk', new Set([
        '/mkgqaa1mfbon.js'
      ])],
    ['asset2.coupangcdn.com', new Set([
        '/jslog.min.js'
      ])],
    ['firebasedynamiclinks.googleapis.com', new Set([
        '/v1/installattribution'
      ])],
    ['api.rc-backup.com', new Set([
        '/adservices_attribution'
      ])],
    ['api.revenuecat.com', new Set([
        '/adservices_attribution'
      ])],
    ['api-d.dropbox.com', new Set([
        '/send_mobile_log'
      ])],
    ['www.google.com', new Set([
        '/log', '/pagead/1p-user-list/'
      ])],
    ['js.stripe.com', new Set([
        '/fingerprinted/'
      ])],
    ['chatgpt.com', new Set([
        '/ces/statsc/flush', '/v1/rgstr'
      ])],
    ['tw.fd-api.com', new Set([
        'DROP:/api/v5/action-log'
      ])],
    ['chatbot.shopee.tw', new Set([
        '/report/v1/log'
      ])],
    ['data-rep.livetech.shopee.tw', new Set([
        '/dataapi/dataweb/event/'
      ])],
    ['shopee.tw', new Set([
        '/dataapi/dataweb/event/', '/abtest/traffic/'
      ])],
    ['api.tongyi.com', new Set([
        '/qianwen/event/track'
      ])],
    ['gw.alipayobjects.com', new Set([
        '/config/loggw/'
      ])],
    ['slack.com', new Set([
        '/api/profiling.logging.enablement', '/api/telemetry', 'DROP:/clog/track/', 'DROP:/api/eventlog.history'
      ])],
    ['slackb.com', new Set([
        'DROP:/'
      ])],
    ['discord.com', new Set([
        'DROP:/api/v10/science', 'DROP:/api/v9/science'
      ])],
    ['browser.events.data.microsoft.com', new Set([
        'DROP:/'
      ])],
    ['mobile.events.data.microsoft.com', new Set([
        'DROP:/'
      ])],
    ['self.events.data.microsoft.com', new Set([
        'DROP:/'
      ])],
    ['watson.telemetry.microsoft.com', new Set([
        'DROP:/'
      ])],
    ['graphql.ec.yahoo.com', new Set([
        '/app/sas/v1/fullsitepromotions'
      ])],
    ['prism.ec.yahoo.com', new Set([
        '/api/prism/v2/streamwithads'
      ])],
    ['analytics.google.com', new Set([
        '/g/collect', '/j/collect'
      ])],
    ['region1.analytics.google.com', new Set([
        '/g/collect'
      ])],
    ['stats.g.doubleclick.net', new Set([
        '/g/collect', '/j/collect'
      ])],
    ['www.google-analytics.com', new Set([
        '/debug/mp/collect', '/g/collect', '/j/collect', '/mp/collect'
      ])],
    ['google.com', new Set([
        '/ads', '/pagead'
      ])],
    ['facebook.com', new Set([
        '/tr', '/tr/'
      ])],
    ['ads.tiktok.com', new Set([
        '/i18n/pixel'
      ])],
    ['business-api.tiktok.com', new Set([
        '/open_api', '/open_api/v1.2/pixel/track', '/open_api/v1.3/event/track', '/open_api/v1.3/pixel/track'
      ])],
    ['analytics.linkedin.com', new Set([
        '/collect'
      ])],
    ['px.ads.linkedin.com', new Set([
        '/collect'
      ])],
    ['ads.bing.com', new Set([
        '/msclkid'
      ])],
    ['ads.linkedin.com', new Set([
        '/li/track'
      ])],
    ['ads.yahoo.com', new Set([
        '/pixel'
      ])],
    ['amazon-adsystem.com', new Set([
        '/e/ec'
      ])],
    ['api.amplitude.com', new Set([
        '/2/httpapi'
      ])],
    ['api.hubspot.com', new Set([
        '/events'
      ])],
    ['api-js.mixpanel.com', new Set([
        '/track'
      ])],
    ['api.mixpanel.com', new Set([
        '/track'
      ])],
    ['api.segment.io', new Set([
        '/v1/page', '/v1/track'
      ])],
    ['c.segment.com', new Set([
        '/v1/track', '/v1/page', '/v1/identify'
      ])],
    ['heap.io', new Set([
        '/api/track'
      ])],
    ['in.hotjar.com', new Set([
        '/api/v2/client'
      ])],
    ['scorecardresearch.com', new Set([
        '/beacon.js'
      ])],
    ['segment.io', new Set([
        '/v1/track'
      ])],
    ['tr.snap.com', new Set([
        '/v2/conversion'
      ])],
    ['ads-api.tiktok.com', new Set([
        '/api/v2/pixel'
      ])],
    ['ads.pinterest.com', new Set([
        '/v3/conversions/events'
      ])],
    ['analytics.snapchat.com', new Set([
        '/v1/batch'
      ])],
    ['cnzz.com', new Set([
        '/stat.php'
      ])],
    ['gdt.qq.com', new Set([
        '/gdt_mview.fcg'
      ])],
    ['hm.baidu.com', new Set([
        '/hm.js'
      ])],
    ['cloudflareinsights.com', new Set([
        '/cdn-cgi/rum'
      ])],
    ['static.cloudflareinsights.com', new Set([
        '/beacon.min.js'
      ])],
    ['bat.bing.com', new Set([
        '/action'
      ])],
    ['metrics.vitals.vercel-insights.com', new Set([
        '/v1/metrics'
      ])],
    ['monorail-edge.shopifysvc.com', new Set([
        '/v1/produce'
      ])],
    ['vitals.vercel-insights.com', new Set([
        '/v1/vitals'
      ])],
    ['pbd.yahoo.com', new Set([
        '/data/logs'
      ])],
    ['plausible.io', new Set([
        '/api/event'
      ])],
    ['analytics.tiktok.com', new Set([
        '/i18n/pixel/events.js'
      ])],
    ['a.clarity.ms', new Set([
        '/collect'
      ])],
    ['d.clarity.ms', new Set([
        '/collect'
      ])],
    ['l.clarity.ms', new Set([
        '/collect'
      ])],
    ['ct.pinterest.com', new Set([
        '/v3'
      ])],
    ['events.redditmedia.com', new Set([
        '/v1'
      ])],
    ['s.pinimg.com', new Set([
        '/ct/core.js'
      ])],
    ['www.redditstatic.com', new Set([
        '/ads/pixel.js'
      ])],
    ['vk.com', new Set([
        '/rtrg'
      ])],
    ['instagram.com', new Set([
        '/logging_client_events'
      ])],
    ['mall.shopee.tw', new Set([
        '/userstats_record/batchrecord'
      ])],
    ['patronus.idata.shopeemobile.com', new Set([
        '/log-receiver/api/v1/0/tw/event/batch', '/event-receiver/api/v4/tw'
      ])],
    ['dp.tracking.shopee.tw', new Set([
        '/v4/event_batch'
      ])],
    ['live-apm.shopee.tw', new Set([
        '/apmapi/v1/event'
      ])],
    ['cmapi.tw.coupang.com', new Set([
        '/featureflag/batchtracking', '/sdp-atf-ads/', '/sdp-btf-ads/', '/home-banner-ads/',
        '/category-banner-ads/', '/plp-ads/'
      ])],
    ['disqus.com', new Set([
        '/api/3.0/users/events', '/j/', '/tracking_pixel/'
      ])],
    ['yahooapis.jp', new Set([
        '/v2/acookie/lookup', '/acookie/'
      ])]
  ])
  },

  KEYWORDS: {
    HIGH_CONFIDENCE: [
    '/ad/', '/ads/', '/adv/', '/advert/', '/banner/', '/pixel/',
    '/tracker/', '/interstitial/', '/midroll/', '/popads/', '/preroll/', '/postroll/'
  ],
    PATH_BLOCK: [
    'china-caa', '/advertising/', '/affiliate/', '/videoads/', '/popup/', '/promoted/',
    '/sponsor/', '/vclick/', '/ads-self-serve/', '/httpdns/', '/d?dn=', '/resolve?host=',
    '/query?host=', '__httpdns__', 'dns-query', '112wan', '2mdn', '51y5',
    '51yes', '789htbet', '96110', 'acs86', 'ad-choices', 'ad-logics',
    'adash', 'adashx', 'adcash', 'adcome', 'addsticky', 'addthis',
    'adform', 'adhacker', 'adinfuse', 'adjust', 'admarvel', 'admaster',
    'admation', 'admdfs', 'admicro', 'admob', 'adnewnc', 'adpush',
    'adpushup', 'adroll', 'adsage', 'adsame', 'adsense', 'adsensor',
    'adserver', 'adservice', 'adsh', 'adskeeper', 'adsmind', 'adsmogo',
    'adsnew', 'adsrvmedia', 'adsrvr', 'adsserving', 'adsterra', 'adsupply',
    'adsupport', 'adswizz', 'adsystem', 'adtilt', 'adtima', 'adtrack',
    'advert', 'advertise', 'advertisement', 'advertiser', 'adview', 'ad-video',
    'advideo', 'adware', 'adwhirl', 'adwords', 'adzcore', 'affiliate',
    'alexametrics', 'allyes', 'amplitude', 'analysis', 'analysys', 'analytics',
    'aottertrek', 'appadhoc', 'appads', 'appboy', 'appier', 'applovin',
    'appsflyer', 'apptimize', 'apsalar', 'baichuan', 'bango', 'bangobango',
    'bidvertiser', 'bingads', 'bkrtx', 'bluekai', 'breaktime', 'bugsense',
    'burstly', 'cedexis', 'chartboost', 'circulate', 'click-fraud', 'clkservice',
    'cnzz', 'cognitivlabs', 'collect', 'crazyegg', 'crittercism', 'cross-device',
    'dealerfire', 'dfp', 'dienst', 'djns', 'dlads', 'dnserror',
    'domob', 'doubleclick', 'doublemax', 'dsp', 'duapps', 'duomeng',
    'dwtrack', 'egoid', 'emarbox', 'en25', 'eyeota', 'fenxi',
    'fingerprinting', 'flurry', 'fwmrm', 'getadvltem', 'getexceptional', 'googleads',
    'googlesyndication', 'greenplasticdua', 'growingio', 'guanggao', 'guomob', 'guoshipartners',
    'heapanalytics', 'hotjar', 'hsappstatic', 'hubspot', 'igstatic', 'inmobi',
    'innity', 'instabug', 'intercom', 'izooto', 'jpush', 'juicer',
    'jumptap', 'kissmetrics', 'lianmeng', 'litix', 'localytics', 'logly',
    'mailmunch', 'malvertising', 'matomo', 'medialytics', 'meetrics', 'mgid',
    'mifengv', 'mixpanel', 'mobaders', 'mobclix', 'mobileapptracking', '/monitoring/',
    'mvfglobal', 'networkbench', 'newrelic', 'omgmta', 'omniture', 'onead',
    'openinstall', 'openx', 'optimizely', 'outstream', 'partnerad', 'pingfore',
    'piwik', 'pixanalytics', 'playtomic', 'polyad', 'popin', 'popin2mdn',
    'programmatic', 'pushnotification', 'quantserve', 'quantumgraph', 'queryly', 'qxs',
    'rayjump', 'retargeting', 'ronghub', 'scorecardresearch', 'scupio', 'securepubads',
    'sensor', 'sentry', 'shence', 'shenyun', 'shoplytics', 'shujupie',
    'smartadserver', 'smartbanner', 'snowplow', 'socdm', 'sponsors', 'spy',
    'spyware', 'statcounter', 'stathat', 'sticky-ad', 'storageug', 'straas',
    'studybreakmedia', 'stunninglover', 'supersonicads', 'syndication', 'taboola', 'tagtoo',
    'talkingdata', 'tanx', 'tapjoy', 'tapjoyads', 'tenmax', 'tapfiliate',
    'tingyun', 'tiqcdn', 'tlcafftrax', 'toateeli', 'tongji', '/trace/',
    'tracker', 'trackersimulator', 'trafficjunky', 'trafficmanager', 'tubemogul', 'uedas',
    'umeng', 'umtrack', 'unidesk', 'usermaven', 'usertesting', 'vast',
    'venraas', 'vilynx', 'vpaid', 'vpon', 'vungle', 'whalecloud',
    'wistia', 'wlmonitor', 'woopra', 'xxshuyuan', 'yandex', 'zaoo',
    'zarget', 'zgdfz6h7po', 'zgty365', 'zhengjian', 'zhengwunet', 'zhuichaguoji',
    'zjtoolbar', 'zzhyyj', '/ad-choices', '/ad-click', '/ad-code', 'ad-conversion',
    '/ad-engagement', 'ad-engagement', '/ad-event', '/ad-events', '/ad-exchange', 'ad-impression',
    '/ad-impression', '/ad-inventory', '/ad-loader', '/ad-logic', '/ad-manager', '/ad-metrics',
    '/ad-network', '/ad-placement', '/ad-platform', '/ad-request', '/ad-response', '/ad-script',
    '/ad-server', '/ad-slot', '/ad-specs', '/ad-system', '/ad-tag', '/ad-tech',
    'ad-telemetry', '/ad-telemetry', '/ad-unit', 'ad-verification', '/ad-verification', '/ad-view',
    'ad-viewability', '/ad-viewability', '/ad-wrapper', '/adframe/', '/adrequest/', '/adretrieve/',
    '/adserve/', '/adserving/', '/fetch_ads/', '/getad/', '/getads/', 'ad-break',
    'ad_event', 'ad_logic', 'ad_pixel', 'ad-call', 'adsbygoogle', 'amp-ad',
    'amp-analytics', 'amp-auto-ads', 'amp-sticky-ad', 'amp4ads', 'apstag', 'google_ad',
    'pagead', 'pwt.js', '/analytic/', '/analytics/', '/api/v2/rum', '/audit/',
    '/beacon/', '/collect?', '/collector/', 'g/collect', '/insight/', '/intelligence/',
    '/measurement', 'mp/collect', '/report/', '/reporting/', '/reports/', '/unstable/produce_batch',
    '/v1/produce', '/bugsnag/', '/crash/', 'debug/mp/collect', '/error/', '/envelope',
    '/exception/', '/stacktrace/', 'performance-tracking', 'real-user-monitoring', 'web-vitals', 'audience',
    'attribution', 'behavioral-targeting', 'cohort', 'cohort-analysis', 'data-collection', 'data-sync',
    'fingerprint', 'session-replay', 'third-party-cookie', 'user-analytics', 'user-behavior', 'user-cohort',
    'user-segment', 'comscore', 'fbevents', 'fbq', 'google-analytics', 'osano',
    'sailthru', 'utag.js', '/apmapi/', 'canvas-fingerprint', 'canvas-fp', '/canvas-fp/',
    'webgl-fingerprint', 'webgl-fp', '/webgl-fp/', 'audio-fingerprint', 'audio-fp', 'font-fingerprint',
    'font-detect-fp'
  ],
    PRIORITY_DROP: new Set([
    '/otel/v1/logs', '/otel/v1/traces', '/otel/v1/metrics', '/agent/v1/logs', '/v1/telemetry', '/v1/metrics',
    '/v1/traces', '/telemetry/'
  ]),
    DROP: new Set([
    '?diag=', '?log=', '-log.', '/diag/', '/log/', '/logging/',
    '/logs/', 'adlog', 'ads-beacon', 'airbrake', 'amp-analytics', '/batch/',
    '/batch?', 'beacon', 'client-event', 'collect', 'collect?', 'collector',
    'crashlytics', 'csp-report', 'data-pipeline', 'error-monitoring', 'error-report', 'heartbeat',
    'ingest', 'intake', 'live-log', 'log-event', 'logevents', 'loggly',
    'log-hl', 'realtime-log', '/rum/', 'server-event', 'uploadmobiledata', 'web-beacon',
    'web-vitals', 'crash-report', 'diagnostic.log', 'profiler', 'stacktrace', 'trace.json',
    '/error_204', 'a=logerror', '/client/events'
  ])
  },

  PARAMS: {
    GLOBAL: new Set([
    'dev_id', 'device_id', 'gclid', 'fbclid', 'ttclid', 'utm_source',
    'utm_medium', 'utm_campaign', 'utm_term', 'utm_content', 'yclid', 'mc_cid',
    'mc_eid', 'srsltid', 'dclid', 'gclsrc', 'twclid', 'lid',
    '_branch_match_id', '_ga', '_gl', '_gid', '_openstat', 'admitad_uid',
    'aiad_clid', 'awc', 'btag', 'cjevent', 'cmpid', 'cuid',
    'external_click_id', 'gad_source', 'gbraid', 'gps_adid', 'iclid', 'igshid',
    'irclickid', 'is_retargeting', 'ko_click_id', 'li_fat_id', 'mibextid', 'msclkid',
    'oprtrack', 'rb_clickid', 'sscid', 'trk', 'usqp', 'vero_conv',
    'vero_id', 'wbraid', 'wt_mc', 'xtor', 'ysclid', 'zanpid',
    'yt_src', 'yt_ad', 's_kwcid', 'sc_cid', 'log_level'
  ]),
    GLOBAL_REGEX: [/^utm_\w+/i, /^ig_[\w_]+/i, /^asa_\w+/i, /^tt_[\w_]+/i, /^li_[\w_]+/i],
    PREFIX_BUCKETS: new Map([
    ['_', [
        '__cf_', '_bta', '_ga_', '_gat_', '_gid_', '_hs',
        '_oly_'
      ]],
    ['a', [
        'action_', 'ad_', 'adjust_', 'aff_', 'af_', 'alg_',
        'at_'
      ]],
    ['b', [
        'bd_', 'bsft_'
      ]],
    ['c', [
        'campaign_', 'cj', 'cm_', 'content_', 'creative_'
      ]],
    ['f', [
        'fb_', 'from_'
      ]],
    ['g', [
        'gcl_', 'guce_'
      ]],
    ['h', [
        'hmsr_', 'hsa_'
      ]],
    ['i', [
        'ir_', 'itm_'
      ]],
    ['l', [
        'li_', 'li_fat_', 'linkedin_'
      ]],
    ['m', [
        'matomo_', 'medium_', 'mkt_', 'ms_', 'mt_', 'mtm'
      ]],
    ['p', [
        'pk_', 'piwik_', 'placement_'
      ]],
    ['r', [
        'ref_'
      ]],
    ['s', [
        'share_', 'source_', 'space_'
      ]],
    ['t', [
        'term_', 'trk_', 'tt_', 'ttc_'
      ]],
    ['v', [
        'vsm_'
      ]]
  ]),
    PREFIXES_REGEX: [/_ga_/i, /^tt_[\w_]+/i, /^li_[\w_]+/i],
    COSMETIC: new Set(['fb_ref', 'fb_source', 'from', 'ref', 'share_id']),
    WHITELIST: new Set(['code', 'id', 'p', 'page', 'product_id', 'q', 'query', 'search', 'session_id', 'state', 'token', 'format', 'lang', 'locale', 'salt', 's']),
    EXEMPTIONS: new Map(),
    SCOPED_EXEMPTIONS: new Map([
    ['104.com.tw', new Map([
        ['/api/', new Set([
            'device_id', 'client_id'
          ])],
        ['/apis/', new Set([
            'device_id'
          ])],
        ['/v2/api/', new Set([
            'device_id'
          ])],
        ['/2.0/', new Set([
            'device_id'
          ])],
        ['!/2.0/ad/', new Set([
            'device_id'
          ])]
        ])]
  ])
  },

  REGEX: {
    PATH_BLOCK: [ /^\/(\w+\/)?ads?\//i, /\/(ad|banner|tracker)\.(js|gif|png)(\?|$)/i ],
    HEURISTIC: [ /[?&](ad|ads|campaign|tracker)_[a-z]+=/i ],
    API_SIGNATURE_BYPASS: [ /\/(api|graphql|trpc|rest)\//i, /\.(json|xml)(\?|$)/i ]
  },

  EXCEPTIONS: {
    SUFFIXES: new Set([
    '.css', '.js', '.jpg', '.jpeg', '.gif', '.png',
    '.ico', '.svg', '.webp', '.woff', '.woff2', '.ttf',
    '.eot', '.mp4', '.mp3', '.mov', '.m4a', '.json',
    '.xml', '.yaml', '.yml', '.toml', '.ini', '.pdf',
    '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.zip', '.rar'
  ]),
    PREFIXES: new Set(['/favicon', '/assets/', '/static/', '/images/', '/img/', '/js/', '/css/']),
    SUBSTRINGS: new Set(['cdn-cgi']),
    SEGMENTS: new Set(['assets', 'static', 'images', 'img', 'css', 'js']),
    PATH_EXEMPTIONS: new Map([
    ['storm.mg', new Set([
        '/_nuxt/track'
      ])],
    ['shopee.tw', new Set([
        '/api/v4/search/search_items', '/api/v4/pdp/get'
      ])],
    ['uber.com', new Set([
        '/go/_events'
      ])],
    ['cmapi.tw.coupang.com', new Set([
        '/vendor-items/'
      ])],
    ['coupangcdn.com', new Set([
        '/image/ccm/banner/', '/image/cmg/oms/banner/'
      ])],
    ['www.google.com', new Set([
        '/url', '/search', '/s2/favicons'
      ])],
    ['play.googleapis.com', new Set([
        '/log/batch'
      ])],
    ['threads.com', new Set([
        '/post/'
      ])],
    ['threads.net', new Set([
        '/post/'
      ])]
  ])
  }
};

const PRECOMPILED_SCANNERS = {
  HIGH_CONFIDENCE: /(\/ad\/|\/ads\/|\/adv\/|\/advert\/|\/banner\/|\/pixel\/|\/tracker\/|\/interstitial\/|\/midroll\/|\/popads\/|\/preroll\/|\/postroll\/)/i,
  PATH_BLOCK: /(china-caa|\/advertising\/|\/affiliate\/|\/videoads\/|\/popup\/|\/promoted\/|\/sponsor\/|\/vclick\/|\/ads-self-serve\/|\/httpdns\/|\/d\?dn=|\/resolve\?host=|\/query\?host=|__httpdns__|dns-query|112wan|2mdn|51y5|51yes|789htbet|96110|acs86|ad-choices|ad-logics|adash|adashx|adcash|adcome|addsticky|addthis|adform|adhacker|adinfuse|adjust|admarvel|admaster|admation|admdfs|admicro|admob|adnewnc|adpush|adpushup|adroll|adsage|adsame|adsense|adsensor|adserver|adservice|adsh|adskeeper|adsmind|adsmogo|adsnew|adsrvmedia|adsrvr|adsserving|adsterra|adsupply|adsupport|adswizz|adsystem|adtilt|adtima|adtrack|advert|advertise|advertisement|advertiser|adview|ad-video|advideo|adware|adwhirl|adwords|adzcore|affiliate|alexametrics|allyes|amplitude|analysis|analysys|analytics|aottertrek|appadhoc|appads|appboy|appier|applovin|appsflyer|apptimize|apsalar|baichuan|bango|bangobango|bidvertiser|bingads|bkrtx|bluekai|breaktime|bugsense|burstly|cedexis|chartboost|circulate|click-fraud|clkservice|cnzz|cognitivlabs|collect|crazyegg|crittercism|cross-device|dealerfire|dfp|dienst|djns|dlads|dnserror|domob|doubleclick|doublemax|dsp|duapps|duomeng|dwtrack|egoid|emarbox|en25|eyeota|fenxi|fingerprinting|flurry|fwmrm|getadvltem|getexceptional|googleads|googlesyndication|greenplasticdua|growingio|guanggao|guomob|guoshipartners|heapanalytics|hotjar|hsappstatic|hubspot|igstatic|inmobi|innity|instabug|intercom|izooto|jpush|juicer|jumptap|kissmetrics|lianmeng|litix|localytics|logly|mailmunch|malvertising|matomo|medialytics|meetrics|mgid|mifengv|mixpanel|mobaders|mobclix|mobileapptracking|\/monitoring\/|mvfglobal|networkbench|newrelic|omgmta|omniture|onead|openinstall|openx|optimizely|outstream|partnerad|pingfore|piwik|pixanalytics|playtomic|polyad|popin|popin2mdn|programmatic|pushnotification|quantserve|quantumgraph|queryly|qxs|rayjump|retargeting|ronghub|scorecardresearch|scupio|securepubads|sensor|sentry|shence|shenyun|shoplytics|shujupie|smartadserver|smartbanner|snowplow|socdm|sponsors|spy|spyware|statcounter|stathat|sticky-ad|storageug|straas|studybreakmedia|stunninglover|supersonicads|syndication|taboola|tagtoo|talkingdata|tanx|tapjoy|tapjoyads|tenmax|tapfiliate|tingyun|tiqcdn|tlcafftrax|toateeli|tongji|\/trace\/|tracker|trackersimulator|trafficjunky|trafficmanager|tubemogul|uedas|umeng|umtrack|unidesk|usermaven|usertesting|vast|venraas|vilynx|vpaid|vpon|vungle|whalecloud|wistia|wlmonitor|woopra|xxshuyuan|yandex|zaoo|zarget|zgdfz6h7po|zgty365|zhengjian|zhengwunet|zhuichaguoji|zjtoolbar|zzhyyj|\/ad-choices|\/ad-click|\/ad-code|ad-conversion|\/ad-engagement|ad-engagement|\/ad-event|\/ad-events|\/ad-exchange|ad-impression|\/ad-impression|\/ad-inventory|\/ad-loader|\/ad-logic|\/ad-manager|\/ad-metrics|\/ad-network|\/ad-placement|\/ad-platform|\/ad-request|\/ad-response|\/ad-script|\/ad-server|\/ad-slot|\/ad-specs|\/ad-system|\/ad-tag|\/ad-tech|ad-telemetry|\/ad-telemetry|\/ad-unit|ad-verification|\/ad-verification|\/ad-view|ad-viewability|\/ad-viewability|\/ad-wrapper|\/adframe\/|\/adrequest\/|\/adretrieve\/|\/adserve\/|\/adserving\/|\/fetch_ads\/|\/getad\/|\/getads\/|ad-break|ad_event|ad_logic|ad_pixel|ad-call|adsbygoogle|amp-ad|amp-analytics|amp-auto-ads|amp-sticky-ad|amp4ads|apstag|google_ad|pagead|pwt\.js|\/analytic\/|\/analytics\/|\/api\/v2\/rum|\/audit\/|\/beacon\/|\/collect\?|\/collector\/|g\/collect|\/insight\/|\/intelligence\/|\/measurement|mp\/collect|\/report\/|\/reporting\/|\/reports\/|\/unstable\/produce_batch|\/v1\/produce|\/bugsnag\/|\/crash\/|debug\/mp\/collect|\/error\/|\/envelope|\/exception\/|\/stacktrace\/|performance-tracking|real-user-monitoring|web-vitals|audience|attribution|behavioral-targeting|cohort|cohort-analysis|data-collection|data-sync|fingerprint|session-replay|third-party-cookie|user-analytics|user-behavior|user-cohort|user-segment|comscore|fbevents|fbq|google-analytics|osano|sailthru|utag\.js|\/apmapi\/|canvas-fingerprint|canvas-fp|\/canvas-fp\/|webgl-fingerprint|webgl-fp|\/webgl-fp\/|audio-fingerprint|audio-fp|font-fingerprint|font-detect-fp)/i,
  CRITICAL_PATH: /(\/accounts\/CheckConnection|\/0\.gif|\/1\.gif|\/pixel\.gif|\/beacon\.gif|\/ping\.gif|\/track\.gif|\/dot\.gif|\/clear\.gif|\/empty\.gif|\/shim\.gif|\/spacer\.gif|\/imp\.gif|\/impression\.gif|\/view\.gif|\/sync\.gif|\/sync\.php|\/match\.gif|\/match\.php|\/utm\.gif|\/event\.gif|\/bk|\/bk\.gif|\/collect|\/events|\/track|\/beacon|\/pixel|\/v1\/collect|\/v1\/events|\/v1\/track|\/v1\/report|\/v1\/logs|\/api\/v1\/logs|\/appbase_report_log|\/stat_log|\/trackcode\/|\/v2\/collect|\/v2\/events|\/v2\/track|\/tp2|\/api\/v1\/collect|\/api\/v1\/events|\/api\/v1\/track|\/api\/v1\/telemetry|\/v1\/event|\/api\/stats\/ads|\/api\/stats\/atr|\/api\/stats\/qoe|\/api\/stats\/playback|\/pagead\/gen_204|\/pagead\/paralleladview|\/tiktok\/pixel\/events|\/linkedin\/insight\/track|\/api\/fingerprint|\/v1\/fingerprint|\/cdn\/fp\/|\/api\/collect|\/api\/track|\/tr\/|\/api\/v1\/event|\/rest\/n\/log|\/action-log|\/ramen\/v1\/events|\/_events|\/report\/v1\/log|\/app\/mobilelog|\/api\/web\/ad\/|\/cdn\/fingerprint\/|\/api\/device-id|\/api\/visitor-id|\/ads\/ga-audiences|\/doubleclick\/|\/google-analytics\/|\/googleadservices\/|\/googlesyndication\/|\/googletagmanager\/|\/tiktok\/track\/|\/__utm\.gif|\/j\/collect|\/r\/collect|\/api\/batch|\/api\/events|\/api\/v2\/event|\/api\/v2\/events|\/collect\?|\/data\/collect|\/events\/track|\/ingest\/|\/ingest\/otel|\/intake|\/p\.gif|\/rec\/bundle|\/t\.gif|\/track\/|\/v1\/pixel|\/v3\/track|\/2\/client\/addlog_batch|\/plugins\/easy-social-share-buttons\/|\/event_report|\/log\/aplus|\/v\.gif|\/ad-sw\.js|\/ads-sw\.js|\/ad-call|\/adx\/|\/adsales\/|\/adserver\/|\/adsync\/|\/adtech\/|\/abtesting\/|\/b\/ss|\/feature-flag\/|\/i\/adsct|\/track\/m|\/track\/pc|\/user-profile\/|cacafly\/track|\/api\/v1\/t|\/sa\.gif|\/api\/v2\/rum|\/batch_resolve|\/acookie\/|\/cookie-sync\/|\/prebid|\/sentry\.|sentry-|\/analytics\.|ga-init\.|gtag\.|gtm\.|ytag\.|connect\.js|\/fbevents\.|\/fbq\.|\/pixel\.|tiktok-pixel\.|ttclid\.|insight\.min\.|\/amplitude\.|\/braze\.|\/chartbeat\.|\/clarity\.|\/comscore\.|\/crazyegg\.|\/customerio\.|\/fullstory\.|\/heap\.|\/hotjar\.|\/inspectlet\.|\/iterable\.|\/logrocket\.|\/matomo\.|\/mixpanel\.|\/mouseflow\.|\/optimizely\.|\/piwik\.|\/posthog\.|\/quant\.|\/quantcast\.|\/segment\.|\/statsig\.|\/vwo\.|\/ad-manager\.|\/ad-player\.|\/ad-sdk\.|\/adloader\.|\/adroll\.|\/adsense\.|\/advideo\.|\/apstag\.|\/criteo-loader\.|\/criteo\.|\/doubleclick\.|\/mgid\.|\/outbrain\.|\/pubmatic\.|\/revcontent\.|\/taboola\.|ad-full-page\.|api_event_tracking|itriweblog\.|adobedtm\.|dax\.js|utag\.|visitorapi\.|newrelic\.|nr-loader\.|perf\.js|essb-core\.|\/intercom\.|\/pangle\.|\/tagtoo\.|tiktok-analytics\.|aplus\.|aplus_wap\.|\/ec\.js|\/gdt\.|\/hm\.js|\/u\.js|\/um\.js|\/bat\.js|beacon\.min\.|plausible\.outbound|abtasty\.|ad-core\.|ad-lib\.|adroll_pro\.|ads-beacon\.|autotrack\.|beacon\.|capture\.|\/cf\.js|cmp\.js|collect\.js|link-click-tracker\.|main-ad\.|scevent\.min\.|showcoverad\.|sp\.js|tracker\.js|tracking-api\.|tracking\.js|user-id\.|user-timing\.|wcslog\.|jslog\.min\.|device-uuid\.|\/plugins\/advanced-ads|\/plugins\/adrotate|gad_script\.|\/atrk\.|\/ai\.0\.|\/wp-content\/plugins\/[^\/]+\/.*(?:ads|ad-inserter|advanced-ads|ipa|quads)\.js(?:\?|$)|\/pagead\/js\/adsbygoogle\.js(?:\?|$)|\/ads\.js(?:\?|$)|\/adrotate\.js(?:\?|$))/i
};

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
