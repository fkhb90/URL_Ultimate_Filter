// ==UserScript==
// @name         URL Ultimate Filter V44.78
// @namespace    http://tampermonkey.net/
// @version      44.78
// @description  SSOT 前端防護盾牌，專業級 UI：極簡盾牌圖示、獨立計數器、點擊外部自動收合機制。
// @author       Jerry
// @match        *://*/*
// @run-at       document-start
// @grant        GM_registerMenuCommand
// ==/UserScript==

(function() {
    'use strict';
/**
 * @file      URL-Ultimate-Filter-Tampermonkey.js
 * @version   44.78 (SSOT Compilation)
 */

const CONFIG = { DEBUG_MODE: false, AC_SCAN_MAX_LENGTH: 600 };
const SCRIPT_VERSION = '44.78';

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
    'browser.events.data.microsoft.com', 'mobile.events.data.microsoft.com', 'self.events.data.microsoft.com', 'onecollector.cloudapp.aria.akadns.net', 'watson.telemetry.microsoft.com', 'admob.com',
    'ads.google.com', 'adservice.google.com', 'adservice.google.com.tw', 'doubleclick.net', 'googleadservices.com', 'googlesyndication.com',
    'crashlyticsreports-pa.googleapis.com', 'firebaselogging-pa.googleapis.com', 'imasdk.googleapis.com', 'measurement.adservices.google.com', 'privacysandbox.googleapis.com', 'business.facebook.com',
    'connect.facebook.net', 'graph.facebook.com', '2o7.net', 'adobedc.net', 'demdex.net', 'everesttech.net',
    'omtrdc.net', '3lift.com', 'adnxs.com', 'advertising.com', 'amazon-adsystem.com', 'bidswitch.net',
    'indexexchange.com', 'media.net', 'sharethrough.com', 'teads.tv', 'crwdcntrl.net', 'exelator.com',
    'eyeota.com', 'krxd.net', 'lotame.com', 'liadm.com', 'rlcdn.com', 'tapad.com',
    'contextweb.com', 'mathtag.com', 'rfihub.com', 'adcolony.com', 'applovin.com', 'chartboost.com',
    'ironsrc.com', 'pangle.io', 'popads.net', 'tapjoy.com', 'unityads.unity3d.com', 'vungle.com',
    'outbrain.com', 'taboola.com', 'app-measurement.com', 'branch.io', 'singular.net', 'ad.etmall.com.tw',
    'ad.line.me', 'ad-history.line.me', 'ads.linkedin.com', 'ads.tiktok.com', 'analytics.tiktok.com', 'cdn.segment.com',
    'clarity.ms', 'fullstory.com', 'inmobi.com', 'inner-active.mobi', 'launchdarkly.com', 'split.io',
    'iadsdk.apple.com', 'metrics.icloud.com', 'ad.impactify.io', 'impactify.media', 'adsv.omgrmn.tw', 'browser.sentry-cdn.com',
    'caid.china-caa.org', 'slackb.com', 'events.tiktok.com', 'ibytedtos.com', 'log.tiktokv.com', 'log16-normal-c-useast1a.tiktokv.com',
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
    'analytics.line.me', 'analytics.slashdotmedia.com', 'analytics.strava.com', 'analytics.yahoo.com', 'api.pendo.io', 'c.clarity.ms',
    'c.segment.com', 'chartbeat.com', 'clicktale.net', 'clicky.com', 'comscore.com', 'customer.io',
    'data.investing.com', 'datadoghq.com', 'dynatrace.com', 'fullstory.com', 'heap.io', 'inspectlet.com',
    'iterable.com', 'keen.io', 'kissmetrics.com', 'loggly.com', 'matomo.cloud', 'mgid.com',
    'mouseflow.com', 'mparticle.com', 'mlytics.com', 'nr-data.net', 'oceanengine.com', 'openx.net',
    'optimizely.com', 'piwik.pro', 'posthog.com', 'quantserve.com', 'revcontent.com', 'rudderstack.com',
    'segment.com', 'semasio.net', 'snowplowanalytics.com', 'statcounter.com', 'statsig.com', 'static.ads-twitter.com',
    'sumo.com', 'sumome.com', 'tealium.com', 'track.hubspot.com', 'track.tiara.daum.net', 'track.tiara.kakao.com',
    'vwo.com', 'yieldlab.net', 'fingerprint.com', 'doubleverify.com', 'iasds.com', 'moat.com',
    'moatads.com', 'sdk.iad-07.braze.com', 'serving-sys.com', 'tw.ad.doubleverify.com', 'agkn.com', 'id5-sync.com',
    'liveramp.com', 'permutive.com', 'tags.tiqcdn.com', 'klaviyo.com', 'marketo.com', 'mktoresp.com',
    'pardot.com', 'instana.io', 'launchdarkly.com', 'raygun.io', 'navify.com', 'cnzz.com',
    'umeng.com', 'talkingdata.com', 'jiguang.cn', 'getui.com', 'mdap.alipay.com', 'loggw-ex.alipay.com',
    'pgdt.gtimg.cn', 'afd.baidu.com', 'als.baidu.com', 'cpro.baidu.com', 'dlswbr.baidu.com', 'duclick.baidu.com',
    'feed.baidu.com', 'h2tcbox.baidu.com', 'hm.baidu.com', 'hmma.baidu.com', 'mobads-logs.baidu.com', 'mobads.baidu.com',
    'nadvideo2.baidu.com', 'nsclick.baidu.com', 'sp1.baidu.com', 'voice.baidu.com', '3gimg.qq.com', 'fusion.qq.com',
    'ios.bugly.qq.com', 'lives.l.qq.com', 'monitor.uu.qq.com', 'pingma.qq.com', 'sdk.e.qq.com', 'wup.imtt.qq.com',
    'appcloud.zhihu.com', 'appcloud2.in.zhihu.com', 'crash2.zhihu.com', 'mqtt.zhihu.com', 'sugar.zhihu.com', 'agn.aty.sohu.com',
    'apm.gotokeep.com', 'cn-huabei-1-lg.xf-yun.com', 'gs.getui.com', 'log.b612kaji.com', 'pc-mon.snssdk.com', 'sensorsdata.cn',
    'stat.m.jd.com', 'trackapp.guahao.cn', 'traffic.mogujie.com', 'wmlog.meituan.com', 'zgsdk.zhugeio.com', 'admaster.com.cn',
    'adview.cn', 'alimama.com', 'getui.net', 'gepush.com', 'gridsum.com', 'growingio.com',
    'igexin.com', 'jpush.cn', 'kuaishou.com', 'miaozhen.com', 'mmstat.com', 'pangolin-sdk-toutiao.com',
    'talkingdata.cn', 'tanx.com', 'umeng.cn', 'umeng.co', 'umengcloud.com', 'youmi.net',
    'zhugeio.com', 'appnext.hs.llnwd.net', 'fusioncdn.com', 'abema-adx.ameba.jp', 'ad.12306.cn', 'ad.360in.com',
    'adroll.com', 'ads.yahoo.com', 'adserver.yahoo.com', 'appnexus.com', 'bluekai.com', 'casalemedia.com',
    'doubleclick.net', 'googleadservices.com', 'googlesyndication.com', 'outbrain.com', 'taboola.com', 'rubiconproject.com',
    'pubmatic.com', 'openx.com', 'smartadserver.com', 'spotx.tv', 'yandex.ru', 'addthis.com',
    'onesignal.com', 'sharethis.com', 'bat.bing.com', 'clarity.ms', 'elads.kocpc.com.tw', 'eservice.emarsys.net'
  ]),
  BLOCK_DOMAINS_WILDCARDS: new Set([
    'sentry.io', 'pidetupop.com', 'cdn-net.com', 'lr-ingest.io', 'aotter.net', 'ssp.yahoo.com',
    'pbs.yahoo.com', 'ay.delivery', 'cootlogix.com', 'ottadvisors.com', 'newaddiscover.com', 'app-ads-services.com',
    'app-measurement.com', 'adjust.com', 'adjust.net', 'appsflyer.com', 'onelink.me', 'branch.io',
    'app.link', 'kochava.com', 'scorecardresearch.com', 'rayjump.com', 'mintegral.net', 'tiktokv.com',
    'byteoversea.com', 'criteo.com', 'criteo.net', 'adservices.google.com'
  ]),

  BLOCK_DOMAINS_REGEX: [
    /^ads?\d*\.(?:ettoday\.net|ltn\.com\.tw)$/i, /^browser-intake-[\w.-]*datadoghq\.(?:com|eu|us)$/i
  ],

  CRITICAL_PATH: {
    GENERIC: [
    '/accounts/CheckConnection', '/0.gif', '/1.gif', '/pixel.gif', '/beacon.gif', '/ping.gif',
    '/track.gif', '/dot.gif', '/clear.gif', '/empty.gif', '/shim.gif', '/spacer.gif',
    '/imp.gif', '/impression.gif', '/view.gif', '/sync.gif', '/sync.php', '/match.gif',
    '/match.php', '/utm.gif', '/event.gif', '/bk', '/bk.gif', '/collect',
    '/events', '/track', '/beacon', '/pixel', '/v1/collect', '/v1/events',
    '/v1/track', '/v1/report', '/v1/logs', '/api/v1/logs', '/appbase_report_log', '/stat_log',
    '/trackcode/', '/v2/collect', '/v2/events', '/v2/track', '/tp2', '/api/v1/collect',
    '/api/v1/events', '/api/v1/track', '/api/v1/telemetry', '/v1/event', '/api/stats/ads', '/api/stats/atr',
    '/api/stats/qoe', '/api/stats/playback', '/pagead/gen_204', '/pagead/paralleladview', '/tiktok/pixel/events', '/linkedin/insight/track',
    '/api/fingerprint', '/v1/fingerprint', '/cdn/fp/', '/api/collect', '/api/track', '/tr/',
    '/beacon', '/api/v1/event', '/rest/n/log', '/action-log', '/ramen/v1/events', '/_events',
    '/report/v1/log', '/app/mobilelog', '/api/web/ad/', '/cdn/fingerprint/', '/api/device-id', '/api/visitor-id',
    '/ads/ga-audiences', '/doubleclick/', '/google-analytics/', '/googleadservices/', '/googlesyndication/', '/googletagmanager/',
    '/tiktok/track/', '/__utm.gif', '/j/collect', '/r/collect', '/api/batch', '/api/events',
    '/api/v1/events', '/api/v1/track', '/api/v2/event', '/api/v2/events', '/collect?', '/data/collect',
    '/events/track', '/ingest/', '/ingest/otel', '/intake', '/p.gif', '/rec/bundle',
    '/t.gif', '/track/', '/v1/pixel', '/v2/track', '/v3/track', '/2/client/addlog_batch',
    '/plugins/easy-social-share-buttons/', '/event_report', '/log/aplus', '/v.gif', '/ad-sw.js', '/ads-sw.js',
    '/ad-call', '/adx/', '/adsales/', '/adserver/', '/adsync/', '/adtech/',
    '/abtesting/', '/b/ss', '/feature-flag/', '/i/adsct', '/track/m', '/track/pc',
    '/user-profile/', 'cacafly/track', '/api/v1/t', '/sa.gif', '/api/v2/rum', '/batch_resolve'
  ],
    SCRIPT_ROOTS: [
    '/prebid', '/sentry.', 'sentry-', '/analytics.', 'ga-init.', 'gtag.',
    'gtm.', 'ytag.', 'connect.js', '/fbevents.', '/fbq.', '/pixel.',
    'tiktok-pixel.', 'ttclid.', 'insight.min.', '/amplitude.', '/braze.', '/chartbeat.',
    '/clarity.', '/comscore.', '/crazyegg.', '/customerio.', '/fullstory.', '/heap.',
    '/hotjar.', '/inspectlet.', '/iterable.', '/logrocket.', '/matomo.', '/mixpanel.',
    '/mouseflow.', '/optimizely.', '/piwik.', '/posthog.', '/quant.', '/quantcast.',
    '/segment.', '/statsig.', '/vwo.', '/ad-manager.', '/ad-player.', '/ad-sdk.',
    '/adloader.', '/adroll.', '/adsense.', '/advideo.', '/apstag.', '/criteo-loader.',
    '/criteo.', '/doubleclick.', '/mgid.', '/outbrain.', '/pubmatic.', '/revcontent.',
    '/taboola.', 'ad-full-page.', 'api_event_tracking', 'itriweblog.', 'adobedtm.', 'dax.js',
    'utag.', 'visitorapi.', 'newrelic.', 'nr-loader.', 'perf.js', 'essb-core.',
    '/intercom.', '/pangle.', '/tagtoo.', 'tiktok-analytics.', 'aplus.', 'aplus_wap.',
    '/ec.js', '/gdt.', '/hm.js', '/u.js', '/um.js', '/bat.js',
    'beacon.min.', 'plausible.outbound', 'abtasty.', 'ad-core.', 'ad-lib.', 'adroll_pro.',
    'ads-beacon.', 'autotrack.', 'beacon.', 'capture.', '/cf.js', 'cmp.js',
    'collect.js', 'link-click-tracker.', 'main-ad.', 'scevent.min.', 'showcoverad.', 'sp.js',
    'tracker.js', 'tracking-api.', 'tracking.js', 'user-id.', 'user-timing.', 'wcslog.',
    'jslog.min.', 'device-uuid.', '/plugins/advanced-ads', '/plugins/adrotate'
  ],
    MAP: new Map([
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
        '/api/v5/action-log'
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
        '/api/profiling.logging.enablement', '/api/telemetry', 'DROP:/clog/track/'
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
    ['discord.com', new Set([
        '/api/v10/science', '/api/v9/science'
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
    'fingerprint', 'retargeting', 'session-replay', 'third-party-cookie', 'user-analytics', 'user-behavior',
    'user-cohort', 'user-segment', 'appier', 'comscore', 'fbevents', 'fbq',
    'google-analytics', 'onead', 'osano', 'sailthru', 'tapfiliate', 'utag.js',
    '/apmapi/', 'canvas-fingerprint', 'canvas-fp', '/canvas-fp/', 'webgl-fingerprint', 'webgl-fp',
    '/webgl-fp/', 'audio-fingerprint', 'audio-fp', 'font-fingerprint', 'font-detect-fp'
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
        ['/v2/api/', new Set([
            'device_id'
          ])],
        ['/2.0/notify/', new Set([
            'device_id'
          ])],
        ['/2.0/user/', new Set([
            'device_id'
          ])],
        ['/2.0/company/', new Set([
            'device_id'
          ])],
        ['/2.0/recommend/', new Set([
            'device_id'
          ])],
        ['/2.0/job/', new Set([
            'device_id'
          ])],
        ['/2.0/apply/', new Set([
            'device_id'
          ])],
        ['/2.0/resume/', new Set([
            'device_id'
          ])],
        ['/2.0/collect/', new Set([
            'device_id'
          ])],
        ['/2.0/favorite/', new Set([
            'device_id'
          ])],
        ['/2.0/config/', new Set([
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
    ['shopee.tw', new Set([
        '/api/v4/search/search_items', '/api/v4/pdp/get'
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
