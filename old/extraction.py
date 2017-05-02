# -*- coding: utf-8 -*-
from __future__ import print_function


import re
import time
import os
import json
import unicodedata
import subprocess
from xml.dom import minidom
from core import decrypt

# configuration

pathfolderFragments = "fragments"
pathfolderImages = "images"
pathfolderinfo = "info"
pathfolderImageMagick = "ImageMagick"
pathJavaScript = "core.js"

refererGoogleArtProject = "http://www.googleartproject.com/"
dureeSleep = 0.5

separateur = "\t"

# content d'une pagea Web


def getcontentUrl(url, referer=""):
    time.sleep(dureeSleep)

    requete = urllib.request.Request(url)
    if referer:
        requete.add_header("Referer", referer)

    print("(%s)" % url)

    return urllib.request.urlopen(requete).read()

# URL d'un fragment d'image, d�cryptage d'un fragment d'image


def getUrlFragment(urlImage, x, y, zoom, timestamp):
    return getUrlFragmentTrue(urlImage, x, y, zoom, timestamp)    


def decrypterFragment(contentFragment):
    return decrypt(contentFragment)

# info sur un table (painter, titre, date...)


def getinfotable(urlpageatable):
    regexJsontable = 'var CURRENT_ARTWORK = new ap.Artwork\((.+)\);'

    infotable = {}

    contentpageatable = getcontentUrl(urlpageatable, refererGoogleArtProject)

    jsontable = json.loads(re.findall(regexJsontable, contentpageatable)[0])

    infotable["urlImage"] = str(jsontable["aggregation_image_url"])
    if infotable["urlImage"][:5] != "http:":
        infotable["urlImage"] = "http:" + infotable["urlImage"]

    infotable["painter"] = jsontable["artist_display_name"]

    infotable["titre"] = jsontable["title"]

    try:
        infotable["date"] = str(jsontable["pretty_display_date"])
    except:
        infotable["date"] = ""

    try:
        infotable["titre original"] = jsontable["facets"]["Original Title"][0]
    except:
        infotable["titre original"] = ""

    try:
        infotable["autre titre"] = jsontable["facets"]["Non-English title"][0]
    except:
        infotable["autre titre"] = ""

    try:
        infotable["mouvements"] = jsontable["facets"]["Style"][0]
    except:
        infotable["mouvements"] = ""

    try:
        infotable["techniques"] = jsontable["facets"]["Medium"][0]
    except:
        infotable["techniques"] = ""

    return infotable

# t�l�chargements des fragments d'image


def getinfoFragments(urlImage, zoom):
    docXml = minidom.parse(urllib2.urlopen(urlImage + "=g"))

    widthFragment = int(docXml.firstChild.attributes["tile_width"].value)
    heightFragment = int(docXml.firstChild.attributes["tile_height"].value)

    zoomMax = int(docXml.firstChild.attributes["full_pyramid_depth"].value) - 1

    if zoom > zoomMax:
        zoom = zoomMax

    xMax = int(docXml.getElementsByTagName("pyramid_level")[zoom].attributes["num_tiles_x"].value)
    yMax = int(docXml.getElementsByTagName("pyramid_level")[zoom].attributes["num_tiles_y"].value)

    return zoom, xMax, yMax, widthFragment, heightFragment


def downloadFragment(urlImage, pathFragment, x, y, zoom):
    timestamp = int(time.time())
    urlFragment = getUrlFragment(urlImage, x, y, zoom, timestamp)

    contentFragment = getcontentUrl(urlFragment, refererGoogleArtProject)

    contentFragment = decrypterFragment(contentFragment)

    fileFragment = open(pathFragment, "wb")
    fileFragment.write(contentFragment)
    fileFragment.close()


def downloadallFragments(urlImage, xMax, yMax, zoom):
    i = 0
    for y in range(yMax):
        for x in range(xMax):
            i = i+1

            pathFragment = os.path.join(pathfolderFragments, "fragment_%s.jpg" % format(i, "03d"))

            downloadFragment(urlImage, pathFragment, x, y, zoom)

# reconstitution de l'image � partir des fragments


def reconstituerImage(namefileImage, xMax, yMax, widthFragment, heightFragment):
    # commandAssembler = (os.path.join(pathfolderImageMagick, "montage.exe")
    #                     + " " + os.path.join(pathfolderFragments, "fragment_[0-9]*.jpg")
    #                     + " -quality 100"
    #                     + " -tile " + str(xMax) + "x" + str(yMax)
    #                     + " -geometry " + str(widthFragment) + "x" + str(heightFragment)
    #                     + " " + os.path.join(pathfolderImages, namefileImage))
    commandAssembler = "montage " + os.path.join(pathfolderFragments, "fragment_[0-9]*.jpg") + " -quality 100"+" -tile " + str(xMax) + "x" + str(yMax)+" -geometry " + str(widthFragment) + "x" + str(heightFragment) + " " + os.path.join(pathfolderImages, namefileImage)

    # commandtrim = (os.path.join(pathfolderImageMagick, "mogrify.exe")
    #                  + " -quality 100"
    #                  + " -trim"
    #                  + " -fuzz 10%"
    #                  + " " + os.path.join(pathfolderImages, namefileImage))
    #
    commandtrim = "mogrify " + " -quality 100" + " -trim" + " -fuzz 10%" + " " + os.path.join(pathfolderImages, namefileImage)
    p1 = subprocess.Popen(commandAssembler, shell=True)  # , creationflags=0x08000000)
    p1.communicate()

    p2 = subprocess.Popen(commandtrim, shell=True)  # , creationflags=0x08000000)
    p2.communicate()

# liste des table d'un painter


def getUrlpageastable(idpainter):
    listeUrlpageastable = []

    urlJsontable = "http://www.googleartproject.com/api/int/gap2/artwork/?canonical_artist=%i&limit=500&offset=0&format=json" % idpainter
    jsontable = json.loads(getcontentUrl(urlJsontable, refererGoogleArtProject))

    for table in jsontable["objects"]:
        listeUrlpageastable.append("http://www.googleartproject.com" + str(table["absolute_url"]))

    return listeUrlpageastable

# normalisation d'un cha�ne de caract�res


def normalize_string(string):
    # encodage UTF-8
    try:
        string = unicode(string)
    except:
        string = unicode(string, "iso-8859-1")

    # suppression des accents
    string = unicodedata.normalize("NFKD", string)

    # encodage ASCII
    string = string.encode("ASCII", "ignore")

    return string


def normalize_filename(string):
    string = normalize_string(string)

    # caract�re non alpha-num�rique => "_"
    string = re.sub("[^0-9a-zA-Z\.\-]", "_", string)

    return string

# t�l�chargement des images et info


def cleanfolder(pathfolder):
    for namefile in os.listdir(pathfolder):
        pathfile = os.path.join(pathfolder, namefile)
        if os.path.isfile(pathfile):
            os.remove(pathfile)


def downloadtable(urlImage, namefileImage, zoom):
    zoom, xMax, yMax, widthFragment, heightFragment = getinfoFragments(urlImage, zoom)

    cleanfolder(pathfolderFragments)  # nettoyage du folder des fragments

    downloadallFragments(urlImage, xMax, yMax, zoom)
    reconstituerImage(namefileImage, xMax, yMax, widthFragment, heightFragment)


def downloadtablepainter(namepainter, idpainter, zoom):
    listeChamps = ["image", "painter", "titre", "date", "titre original", "autre titre", "mouvements", "techniques"]

    fileinfo = open(os.path.join(pathfolderinfo, normalize_filename(namepainter) + ".csv"), "w")
    fileinfo.write(separateur.join(listeChamps) + "\n")

    listeUrlpageastable = getUrlpageastable(idpainter)

    print("### %s : %i table" % (namepainter, len(listeUrlpageastable)))

    i = 0
    for urlpageatable in listeUrlpageastable:
        i = i+1

        print("# %s, table %i/%i : %s" % (namepainter, i, len(listeUrlpageastable), urlpageatable))

        infotable = getinfotable(urlpageatable)
        urlImage = infotable["urlImage"]

        namefileImage = normalize_filename(namepainter) + "-" + format(i, "03d") + ".jpg"

        downloadtable(urlImage, namefileImage, zoom)

        infotable["image"] = namefileImage
        fileinfo.write(separateur.join([normalize_string(infotable[champ]) for champ in listeChamps]) + "\n")

    fileinfo.close()

# fonctions principales


def downloadartwork(urlartwork, namefileImage, zoom):
    contentpageartwork = getcontentUrl(urlartwork, refererGoogleArtProject)

    regexUrlImage = 'data-image-url="([^"]+)'
    print(re.findall(regexUrlImage, contentpageartwork))
    urlImage = re.findall(regexUrlImage, contentpageartwork)[0]
    if urlImage.find("http:") == -1:  # add this code
        urlImage = "http:" + urlImage  # add this code
    downloadtable(urlImage, normalize_filename(namefileImage), zoom)


def downloadartist(urlartist, zoom):
    contentpageartist = getcontentUrl(urlartist, refererGoogleArtProject)

    regexnameartist = re.compile("""data-artist-name=\"([^\"]+)\"""")
    regexIdartist = re.compile("""data-artist-id=\"([^\"]+)\"""")

    nameartist = re.findall(regexnameartist, contentpageartist)[0]
    idartist = int(re.findall(regexIdartist, contentpageartist)[0])

    nameartist

    downloadtablepainter(nameartist, idartist, zoom)

# ex�cution du script


'''
timeout=20
a=[]
with open("images.txt","r") as f:
    for line in f:
        a.append(line)
jjj=[]
for i in a:
    if i[0]=="#":
        continue
    if len(i)<25:
        if i.split(" ")[0]=="timeout":
            try:
                timeout=int(i.split(" ")[1])
            except:
                pass
            continue
  jjj.append(	[	i.split(" ")[0],	i.split(" ")[1],	int(i.split(" ")[2])]	)
for i in jjj:
    downloadartwork(i[0], i[1], i[2])
    time.sleep(timeout)
'''
