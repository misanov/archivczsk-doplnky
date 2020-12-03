# -*- coding: UTF-8 -*-
# /*
# *  Copyright (C) 2020 Michal Novotny https://github.com/misanov
# *
# *
# *  This Program is free software; you can redistribute it and/or modify
# *  it under the terms of the GNU General Public License as published by
# *  the Free Software Foundation; either version 2, or (at your option)
# *  any later version.
# *
# *  This Program is distributed in the hope that it will be useful,
# *  but WITHOUT ANY WARRANTY; without even the implied warranty of
# *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# *  GNU General Public License for more details.
# *
# *  You should have received a copy of the GNU General Public License
# *  along with this program; see the file COPYING.  If not, write to
# *  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
# *  http://www.gnu.org/copyleft/gpl.html
# *
# */
from Plugins.Extensions.archivCZSK.archivczsk import ArchivCZSK
from Plugins.Extensions.archivCZSK.engine.tools.util import toString
from Plugins.Extensions.archivCZSK.engine import client

import cookielib,urllib2,urlparse,re,rfc822,time,util,resolver,json,datetime
from provider import ContentProvider
from provider import ResolveException
import xbmcprovider
import util

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36"

def writeLog(msg, type='INFO'):
	try:
		from Components.config import config
		f = open(os.path.join(config.plugins.archivCZSK.logPath.getValue(),'ec.log'), 'a')
		dtn = datetime.datetime.now()
		f.write(dtn.strftime("%d.%m.%Y %H:%M:%S.%f")[:-3] + " [" + type + "] %s\n" % msg)
		f.close()
	except:
		pass

class LCContentProvider(ContentProvider):

	def __init__(self, username=None, password=None, filter=None, tmp_dir='/tmp'):
		ContentProvider.__init__(self, 'LiveCam', 'https://www.earthcam.com/', username, password, filter, tmp_dir)
		self.cp = urllib2.HTTPCookieProcessor(cookielib.LWPCookieJar())
		self.init_urllib()

	def init_urllib(self):
		opener = urllib2.build_opener(self.cp)
		urllib2.install_opener(opener)

	def capabilities(self):
		return ['categories', 'resolve', 'search']

	def search(self, keyword):
		return self.list(self.base_url+'search/search_results.php?s1=1&_sbox=1&term=%s&search_engine_type=ftsearch&advanced_search=false&perPage=16&camNumAdjust=1&trendingCams=1'%urllib2.quote(keyword))

	def categories(self):
		result = []
		#YOUTUBE TODO
		#https://camstreamer.com/live/stream/12875-live-from-prague-czech-republic
		#https://www.youtube.com/watch?v=s4SiFUNYdTs&ab_channel=SkylineWebcams
		#https://www.youtube.com/watch?v=eE6VVJ3hvv8&ab_channel=ILoveYouVenice
		#https://worldcams.tv/italy/venice/rialto-bridge
		cams = {
			'01Prague (Czech Republic)': 'https://videos-3.earthcam.com/fecnetwork/14191.flv/playlist.m3u8',
			'02Time Square, NY (USA)': 'https://videos-3.earthcam.com/fecnetwork/15559.flv/playlist.m3u8',
			'03Moscow (Russia)': 'https://videos-3.earthcam.com/fecnetwork/moscowHD1.flv/playlist.m3u8',
			'04Dubai (UAE)': 'https://videos-3.earthcam.com/fecnetwork/5868.flv/playlist.m3u8',
			'05Washington, D.C. (USA)': 'https://videos-3.earthcam.com/fecnetwork/capitolcam1.flv/playlist.m3u8',
			'06Budapest (Hungary)': 'https://videos-3.earthcam.com/fecnetwork/15041.flv/playlist.m3u8',
			'07Miami Beach, FL (USA)': 'https://videos-3.earthcam.com/fecnetwork/13862.flv/playlist.m3u8',
			'08Abbey Road, London (UK)': 'https://videos-3.earthcam.com/fecnetwork/AbbeyRoadHD1.flv/playlist.m3u8',
			'09Dublin (Ireland)': 'https://videos-3.earthcam.com/fecnetwork/4054.flv/playlist.m3u8',
			'10Ceuta (Spain)': 'https://videos-3.earthcam.com/fecnetwork/ceuta1.flv/playlist.m3u8',
			'11Tokyo (Japan)': 'https://videos-3.earthcam.com/fecnetwork/tokyo1.flv/playlist.m3u8',
			'12World Trade Center (USA)': 'https://videos-3.earthcam.com/fecnetwork/10874.flv/playlist.m3u8',
			'13Niagara Falls (Canada)': 'https://videos-3.earthcam.com/fecnetwork/4559.flv/playlist.m3u8',
			'14Toronto (Canada)': 'https://videos-3.earthcam.com/fecnetwork/9299.flv/playlist.m3u8',
		}
		for key in sorted(cams):
			item = self.video_item()
			item['title'] = key[2:]
			item['url'] = cams[key]
			result.append(item)
		return result

	def list(self, url):
		headers = {"referer": self.base_url, "User-Agent": UA }
		result = []
		# vyhledat
		if 'search/' in url:
			httpdata = util.request(url,headers=headers)
			data = json.loads(httpdata)
			if "item_data" in data:
				for one in data["item_data"]:
					if "earthcam.com" not in one["db_url"]: continue
					item = self.dir_item()
					item['title'] = re.sub('<[^<]+?>', '', one['title']+' ('+one['cam_location']+')').replace('EarthCam: ','')
					item['url'] = one["db_url"]
					result.append(item)
					print item['url']
			return result
		# seznam kamer streamu
		else:
			html = util.request(url,headers=headers)
			titles = re.findall('"title":"(.*?)"', html, re.S)
			thumbs = re.findall('"thumbnail_512":"(.*?)"', html, re.S)
			doms = re.findall('"html5_streamingdomain":"(.*?)"', html, re.S)
			paths = re.findall('"html5_streampath":"(.*?)"', html, re.S)
			for i in range(len(doms)):
				if not paths[i]: continue
				it = self.video_item()
				it['title'] = titles[i]
				it['url'] = (doms[i]+paths[i]).replace("\\","")
				it['img'] = thumbs[i] if thumbs[i] else None
				it['plot'] = ""
				result.append(it)
				print it['url']
			return result
		return []

	def resolve(self, item, captcha_cb=None, select_cb=None):
		result = []
		if "earthcam" in item['url']:
			item['headers'] = {"referer": self.base_url}
		result.append(item)
		return result

__scriptid__ = 'plugin.video.livecam'
__scriptname__ = 'LiveCam'
__addon__ = ArchivCZSK.get_xbmc_addon(__scriptid__)
__language__ = __addon__.getLocalizedString
addon_userdata_dir = __addon__.getAddonInfo('profile')+'/'
settings = {'quality':__addon__.getSetting('quality')}
provider = LCContentProvider(tmp_dir='/tmp')
xbmcprovider.XBMCMultiResolverContentProvider(provider, settings, __addon__, session).run(params)
