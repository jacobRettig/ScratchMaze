#Have completed complicated calculation stuff but need to put everything together formated with filler stuff to scratchProject
#also make sure to limit AARects' side lengths by splitting up ones that are too large

import urllib2, pip, zipfile, json
from sys import exit, argv
from os import path, makedirs, listdir, walk, remove
from functools import reduce
from zipfile import ZipFile, ZIP_DEFLATED
from shutil import rmtree
from hashlib import md5
from numbers import Number

testIPAddress = 'http://www.google.com/'
tmp = 'tmp'


def zipDir(fileName, dirName):
    with ZipFile(fileName, 'w', ZIP_DEFLATED) as zipF:
        for root, dirs, files in walk(dirName):
            for file in files:
                zipF.write(path.join(root, file))

def delWithPerm(filePath, askPermission=True):
    if path.exists(filePath):
        isPermission = '' if askPermission else 'y'
        while isPermission not in ('y', 'n'):
            isPermission = raw_input('Warning: "{}" already exists, may I delete it? (y/n) : '.format(filePath)).lower()
        if isPermission == 'y':
            if path.isfile(filePath):
                remove(filePath)
            else:
                rmtree(filePath)
            if path.exists(filePath):
                print('Error: Unknown problem trying to delete "{}" after getting permission'.format(filePath))
                return False
            else:
                print('File "{}" deleted'.format(filePath))
                return True
        else:
            print('Permission denied')
            return False
    else:
        return True

def getInput(varName):
    confirmation, val = '', ''
    while confirmation != 'y':
        val = raw_input('Please input value for {} : '.format(varName))
        confirmation = ''
        while confirmation not in ('y', 'n'):
            confirmation = raw_input('Confirm {}={} (y/n) : '.format(varName, val))
    return val


def prepareModule(moduleName):
    try:
        pip.main(['install', '-U', moduleName])
        return True
    except:
        print('module {} failed to install and update'.format(moduleName))
        return False

def isInternetOn(IPAddress, timeout=1):
    try:
        response = urllib2.urlopen(IPAddress, timeout=timeout)
        return True
    except urllib2.URLError as err:
        print('{}\nfailed to connect to test server {} (timeout={})'.format(err, IPAddress, timeout))
        return False

def isInDataFormatted(data):
    def isItemFormatted(item):
        keysAndValues = (('back', unicode), ('ball', unicode), ('goal', unicode), ('maze', unicode), ('goalX', Number), ('goalY', Number))
        return isinstance(item, dict) and len(item) == len(keysAndValues) and all(keyVal[0] in item.keys() and isinstance(item[keyVal[0]], keyVal[1]) for keyVal in keysAndValues)
    return isinstance(data, list) and all(isItemFormatted(item) for item in data)

def getImageMD5(dirPath, imageName, imageExtension):
    md5Name = ''
    with open('{}/{}.{}'.format(dirPath, imageName, imageExtension), 'rb') as f:
        md5Name = '{}.{}'.format(md5(f.read()).hexdigest(), imageExtension)
    return md5Name

def fitImage(img):
    pix = img.load()

    def isEmpty(x, y):
        return pix[x, y][3] == 0

    checkCell = lambda index, otherIndex, axis:isEmpty(index, otherIndex) if axis == 0 else isEmpty(otherIndex, index)
    
    coord = [0, 0]
    lengths = [img.size[0], img.size[1]]
    isOffsets = [False, False]
    while lengths[0] > 0:
        if all(isEmpty(coord[0], y) for y in range(coord[1], coord[1] + lengths[1])):
            coord[0] += 1
            lengths[0] -= 1
        else:
            break
    while lengths[1] > 0:
        if all(isEmpty(x, coord[1]) for x in range(coord[0], coord[0] + lengths[0])):
            coord[1] += 1
            lengths[1] -= 1
        else:
            break

    while lengths[0] > 0:
        if all(isEmpty(coord[0] + lengths[0] - 1, y) for y in range(coord[1], coord[1] + lengths[1])):
            lengths[0] -= 1
        else:
            break
    while lengths[1] > 0:
        if all(isEmpty(x, coord[1] + lengths[1] - 1) for x in range(coord[0], coord[0] + lengths[0])):
            lengths[1] -= 1
        else:
            break
    return img.crop((coord[0], coord[1], coord[0] + lengths[0] - 1, coord[1] + lengths[1] - 1))

def mkImgFitScreen(img, displaySize):
    size1 = (displaySize[0], displaySize[0]*img.size[1]/img.size[0])
    size2 = (displaySize[1]*img.size[0]/img.size[1], displaySize[1])
    
    if size1[1] < displaySize[1]:
        return img.resize(size2, Image.LANCZOS)
    else:
        return img.resize(size1, Image.LANCZOS)


def genChunks(level, img, nImages, filePath, chunkSize):
    pix = img.load()
    nChunks = tuple(1 + (img.size[i] - 1)//chunkSize for i in range(2))

    def isEmpty(x, y):
        return pix[x, y][3] == 0

    def fitChunk(indexX, indexY):
        checkCell = lambda index, otherIndex, axis:isEmpty(index, otherIndex) if axis == 0 else isEmpty(otherIndex, index)
        getCoord = lambda index, axis:img.size[axis]*index/nChunks[axis]
        
        indexes = (indexX, indexY)
        coord = [indexX*img.size[0]/nChunks[0], indexY*img.size[1]/nChunks[1]]
        lengths = [(indexX + 1)*img.size[0]/nChunks[0], (indexY + 1)*img.size[1]/nChunks[1]]
        for i in range(2):
            lengths[i] -= coord[i]
        isOffsets = list((False, False))

        while lengths[0] > 0:
            if all(isEmpty(coord[0], y) for y in range(coord[1], coord[1] + lengths[1])):
                coord[0] += 1
                lengths[0] -= 1
            else:
                break
        while lengths[1] > 0:
            if all(isEmpty(x, coord[1]) for x in range(coord[0], coord[0] + lengths[0])):
                coord[1] += 1
                lengths[1] -= 1
            else:
                break

        while lengths[0] > 0:
            if all(isEmpty(coord[0] + lengths[0] - 1, y) for y in range(coord[1], coord[1] + lengths[1])):
                lengths[0] -= 1
            else:
                break
        while lengths[1] > 0:
            if all(isEmpty(x, coord[1] + lengths[1] - 1) for x in range(coord[0], coord[0] + lengths[0])):
                lengths[1] -= 1
            else:
                break
        return (coord[0], coord[1], lengths[0], lengths[1])

    def genInfo(AARect, nImages):
        subImg = img.crop((AARect[0], AARect[1], AARect[0] + AARect[2], AARect[1] + AARect[3]))
        info = tuple((AARect[0] + (AARect[2] - 1)/2 - img.size[0]/2, img.size[1]/2 - AARect[1] - (AARect[3] - 1)/2, mkCostume('level{}'.format(level), nImages, subImg, filePath)))
        del subImg
        return info

    AARects = list(list(fitChunk(x, y) for x in range(nChunks[0])) for y in range(nChunks[1]))
    AARects = reduce(lambda a,b:a + b, AARects)
    #AARects = filter(lambda AARect:AARect[2] > 0 and AARect[3] > 0, AARects)
    AARectsCompleted = list()
    for AARect in AARects:
        if AARect[2] > 0 and AARect[3] > 0:
            AARectsCompleted.append(genInfo(AARect, nImages))
            nImages += 1
    return nImages, AARectsCompleted

def combineChunks(newChunks, oldChunks, level):
    i = 0
    for chunk in newChunks:
        if i + 1 > len(oldChunks):
            oldChunks.append(dict())
        oldChunks[i][level] = chunk
        i += 1
    return oldChunks


def mkVar(name, value):
    return {'name':name, 'value':value, 'isPersistent':False}

def mkCostume(name, indexNumber, img, filePath):
    costume = {'costumeName':name, 'baseLayerID':indexNumber, 'rotationCenterX':int(img.size[0]/2), 'rotationCenterY':int(img.size[1]/2)}
    if not delWithPerm('{}/{}.png'.format(filePath, indexNumber), False):
        print('Failure when making costume')
        if not delWithPerm(filePath, False):
            print('Failed to clean up')
        exit()
    img.save('{}/{}.png'.format(filePath, indexNumber), 'PNG')
    costume['baseLayerMD5'] = getImageMD5(filePath, indexNumber, 'png')
    return costume

def mkSprite(name, spriteIndex):
    return {'objName':name, 'variables':list(), 'lists':list(), 'scripts':list(), 'scriptComments':list(), 'sounds':list(), 'costumes':list(),
            'CurrentCostumeIndex':0, 'scratchX':0, 'scratchY':0, 'scale':1.0, 'direction':0.0, 'rotationStyle':'none', 'isDraggable':False,
            'indexInLibrary':spriteIndex, 'visible':False, 'spriteInfo':{}}

def mkList(name, contents):
    return {'listName':name, 'contents':contents, 'isPersistent':False, 'x':0, 'y':0, 'width':1, 'height':1, 'visible':False}

def mkVarMonitor(name, target):
    return {'target':target, 'cmd':'getVar:', 'param':name, 'color':15629590, 'label':'{}: {}'.format(target, name), 'mode':1,
            'x':0, 'y':0, 'visible':False, 'sliderMin':0, 'sliderMax':100, 'isDiscrete':True}

def scriptGetX():
    return ['+', ['readVariable', 'ballX'], ['getLine:ofList:', ['+', ['readVariable', 'level'], 1], 'starting X']]
def scriptGetY():
    return ['+', ['readVariable', 'ballY'], ['getLine:ofList:', ['+', ['readVariable', 'level'], 1], 'starting Y']]

def scriptCheckBounds():
    return ['|',
             ['|',
                 ['>', scriptGetX(), ['-', ['readVariable', 'maxX'], ['readVariable', 'velocity']]],
                 ['<', scriptGetX(), ['+', ['readVariable', 'minX'], ['readVariable', 'velocity']]]],
             ['|',
                 ['>', scriptGetY(), ['-', ['readVariable', 'maxY'], ['readVariable', 'velocity']]],
                 ['<', scriptGetY(), ['+', ['readVariable', 'minY'], ['readVariable', 'velocity']]]]]

def mkGoalScripts(numLevels):
    initScript = [0, 0, [['whenGreenFlag'], ['hide'], ['setRotationStyle', 'don\'t rotate'],
       ['gotoX:y:',
           ['+', ['readVariable', 'ballX'], ['getLine:ofList:', ['+', ['readVariable', 'level'], 1], 'starting X']],
           ['+', ['readVariable', 'ballY'], ['getLine:ofList:', ['+', ['readVariable', 'level'], 1], 'starting Y']]]]]

    def genLevelChangeScript(currentLevel):
        if currentLevel >= numLevels:
            return [None]
        else:
            return ['doIfElse',
                    ['=', currentLevel, ['readVariable', 'level']],
                    [['lookLike:', 'level{}'.format(currentLevel + 1)], ['show']],
                    [genLevelChangeScript(currentLevel + 1)]]

    levelChangeScript = [0, 0, [['whenIReceive', 'lvlChange'], ['hide'], genLevelChangeScript(0)]]

    updateMapScript = [0, 0, [['whenIReceive', 'updateMap'], ['doIfElse',
        scriptCheckBounds(), [['hide']], [['show']]], ['gotoX:y:', scriptGetX(), scriptGetY()],
        ['doIf',
            ['touching:', 'ball'],
            [['setVar:to:', 'level', ['+', 1, ['readVariable', 'level']]], ['broadcast:', 'lvlChange']]]]]
    return [initScript, levelChangeScript, updateMapScript]


def mkBallScripts(numLevels):
    initScript = [0, 0, [['whenGreenFlag'], ['hide'], ['comeToFront'], ['setRotationStyle', 'don\'t rotate'],
        ['setVar:to:', 'maxY', 180], ['setVar:to:', 'minY', -180], ['setVar:to:', 'maxX', 240], ['setVar:to:', 'minX', -240],
        ['setVar:to:', 'velocity', 2], ['setVar:to:', 'level', 0], ['setVar:to:', 'number of levels', numLevels],
        ['setVar:to:', 'hasControl', 1], ['setVar:to:', 'isGameOver', 0], ['broadcast:', 'lvlChange']]]
    
    arrowScripts = list([0, 0, [['whenKeyPressed', arrowKey], 
        ['doIf', 
            ['=', ['readVariable', 'hasControl'], 1],
            [['doIf', 
                ['=', ['readVariable', 'isGameOver'], 0], 
                [['setVar:to:', 'isMotionForward', 1], ['setVar:to:', 'lastMovement', directionNumber], ['broadcast:',
                    'updateMap']]]]]]] for arrowKey, directionNumber in (
                    ('up arrow', 1), ('down arrow', 0), ('right arrow', 2), ('left arrow', 3)))

    updateMapScript = [0, 0, [['whenIReceive', 'updateMap'], 
        ['doIf',
            ['=', 0, ['readVariable', 'isMotionForward']],
            [['setVar:to:', 'velocity', ['-', 0, ['readVariable', 'velocity']]]]],
        ['doIfElse',
            ['=', 0, ['readVariable', 'lastMovement']],
            [['changeVar:by:', 'ballY', ['readVariable', 'velocity']]],
            [['doIfElse',
                ['=', 1, ['readVariable', 'lastMovement']],
                [['changeVar:by:', 'ballY', ['-', 0, ['readVariable', 'velocity']]]],
                [['doIfElse',
                    ['=', 2, ['readVariable', 'lastMovement']],
                    [['changeVar:by:', 'ballX', ['-', 0, ['readVariable', 'velocity']]]],
                    [['changeVar:by:', 'ballX', ['readVariable', 'velocity']]]]]]]],
        ['doIf',
            ['=', 0, ['readVariable', 'isMotionForward']],
            [['setVar:to:', 'velocity', ['-', 0, ['readVariable', 'velocity']]]]]]]

    def genLevelChangeScript(numLevel):
        if numLevel >= numLevels:
            return [None]
        else:
            return ['doIfElse', ['=', numLevel, ['readVariable', 'level']], [['startScene', 'level{}'.format(numLevel + 1)],
                ['lookLike:', 'level{}'.format(numLevel + 1)], ['show']], [genLevelChangeScript(numLevel + 1)]]


    levelChangeScript = [0, 0, [['whenIReceive', 'lvlChange'], ['gotoX:y:', 0, 0], ['setVar:to:', 'ballX', 0],
            ['setVar:to:', 'ballY', 0], ['setVar:to:', 'lastMovement', 0], ['hide'], genLevelChangeScript(0),
            ['doIfElse',
                ['=', ['readVariable', 'level'], ['readVariable', 'number of levels']],
                [['say:', 'You win!'], ['setVar:to:', 'isGameOver', 1]],
                [['broadcast:', 'updateMap']]]]]
    return arrowScripts + [levelChangeScript, initScript, updateMapScript]

def mkWallSpriteScripts(wallData, maxLevel):
    initScript = [0, 0, [['whenGreenFlag'], ['hide'], ['setRotationStyle', 'don\'t rotate']]]

    def genLvlChangeScript(level):
        if level > maxLevel:
            return ['setVar:to:', 'isUsed', 0]
        elif level in wallData.keys():
            return ['doIfElse',
                ['=', level - 1, ['readVariable', 'level']],
                [['setVar:to:', 'isUsed', 1], ['lookLike:', 'level{}'.format(level)], ['show']],
                [genLvlChangeScript(level + 1)]]
        else:
            return genLvlChangeScript(level + 1)

    lvlChangeScript = [0, 0, [['whenIReceive', 'lvlChange'], ['setVar:to:', 'initiated touch', 0], ['hide'], genLvlChangeScript(0)]]
    
    updateMapScript = [0, 0, [['whenIReceive', 'updateMap'], ['doIf',
        ['=', 1, ['readVariable', 'isUsed']],
            [['doIfElse',
            scriptCheckBounds(), [['hide']], [['show']]], ['gotoX:y:', scriptGetX(), scriptGetY()],
            ['doIfElse',
                ['touching:', 'ball'],
                [['setVar:to:', 'hasControl', 0], ['setVar:to:', 'initiated touch', 1], ['setVar:to:', 'isMotionForward', 0],
                    ['doBroadcastAndWait', 'updateMap']],
                [['doIf',
                    ['=', 1, ['readVariable', 'initiated touch']],
                    [['setVar:to:', 'hasControl', 1], ['setVar:to:', 'initiated touch', 0]]]]]]]]]
    return [initScript, lvlChangeScript, updateMapScript]



def mkWallSprite(wallIndex, spriteIndex, wallData, maxLevel):
    wall = mkSprite('wallSprite{}'.format(wallIndex), spriteIndex)
    wall['variables'] = [mkVar('isUsed', 1), mkVar('initiated touch', 0)]
    wall['lists'] = [
            mkList('starting X', list(wallData[i + 1][0] if i + 1 in wallData.keys() else 100 for i in range(maxLevel + 1))),
            mkList('starting Y', list(wallData[i + 1][1] if i + 1 in wallData.keys() else 100 for i in range(maxLevel + 1)))]
    for wallItem in wallData.values():
        wall['costumes'].append(wallItem[2])
    wall['scripts'] = mkWallSpriteScripts(wallData, maxLevel)
    return wall 
    

if __name__ == '__main__':
    if len(argv) not in(2, 3):
        print('invalid number of arguments ({}), arguments should be [file path to JSON table containing input for program\'s generation] [(Optional) Number for timeout to try to update modules (won\'t update if no number is provided)]'.format(len(argv)))
        exit()
    elif len(argv) == 3:
        if not isInternetOn(testIPAddress, int(argv[2])):
            exit()
        elif not prepareModule('pip'):
            exit()
        elif not prepareModule('PIL'):
            exit()
        else:
            print('Modules all updated\n')

    if not path.isfile(argv[1]):
        print('Provided path to generation data "{}" is invalid'.format(argv[1]))
        exit()
    else:
        print('Using file at "{}" for JSON table that holds image paths and positions'.format(argv[1]))
    
    inData = None
    with open(argv[1], 'r') as f:
        inData = json.load(f)
    if not isInDataFormatted(inData):
        print('inData incorrectly formatted TODO:put instructions here on the correct format')
        exit()

    from PIL import Image

    #prepare working folder
    if not delWithPerm(tmp):
        print('Failure')
        exit()
    makedirs(tmp)
    
    chunkSize = int(getInput('chunk size (larger chunks means fewer sprites)'))
    velocity = int(getInput('velocity (I recommend 7)'))
    displaySize = (480, 360)
    print('display is size ({}, {})'.format(displaySize[0], displaySize[1]))

    prj = {
            'objName':'Stage',
            'variables':[mkVar('ballX', 0), mkVar('ballY', 0), mkVar('velocity', velocity), mkVar('level', 0), mkVar('lastMovement', 1), mkVar('isMotionForward', 1),
                mkVar('isGameOver', 0), mkVar('minX', -240), mkVar('maxX', 240), mkVar('minY', -180), mkVar('maxY', 180), mkVar('hasControl', 1)],
            'currentCostumeIndex':0,
            'costumes':list(),
            'scripts':list(),
            'scriptComments':list(),
            'penLayerID':0,
            'tempoBDM':60,
            'videoAlpha':0.5,
            'sounds':list(),
            'children':list(mkVarMonitor(name, 'Stage') for name in ('ballX', 'ballY', 'velocity', 'level', 'lastMovement', 'isMotionForward', 'number of levels',
                'isGameOver', 'hasControl')),
            'info':{
                'flashVersion':'WIN 23,0,0,162',
                'scriptCount':17,
                'projectID':'121315981',
                'swfVersion':'v449',
                'videoOn':False,
                'hasCloudData':False,
                'userAgent':'Mozilla\\/5.0 (Windows NT 10.0; WOW64) AppleWebKit\\/537.36 (KHTML, like Gecko) Chrome\\/52.0.2743.116 Safari\\/537.36',
                'spriteCount':0
                }
            }

    #generate pen stuff
    if not delWithPerm('{}/0.png'.format(tmp), False):
        print('Failure')
        if not delWithPerm(tmp, False):
            print('Failed to clean up')
        exit()
    Image.new('RGBA', displaySize, color=(0,0,0,0)).save('{}/0.png'.format(tmp))
    prj['baseLayerMD5'] = getImageMD5(tmp, 0, 'png')

    wallSprites = list()
    wallImagePaths = list()
    ballSprite = mkSprite('ball', 1)
    goalSprite = mkSprite('goal', 0)
    goalXs, goalYs = list(), list()

    imageIndex = 1

    level = 0
    while level < len(inData):
        print('\nprocessing level {}'.format(level))

        #bgImgPath = getInput('background image path (or \'0\' when done)')
        print('Background Image = {}'.format(inData[level]['back']))
        bgImgPath = inData[level]['back']
        if bgImgPath == '0':
            break
        else:
            prj['costumes'].append(mkCostume('level{}'.format(level + 1), imageIndex, mkImgFitScreen(Image.open(bgImgPath), displaySize), tmp))
            imageIndex += 1
    
        

        #ballSprite['costumes'].append(mkCostume('level{}'.format(level + 1), imageIndex, fitImage(Image.open(getInput('ball image path'))), tmp))
        print('Ball Image = {}'.format(inData[level]['ball']))
        ballSprite['costumes'].append(mkCostume('level{}'.format(level + 1), imageIndex, fitImage(Image.open(inData[level]['ball'])), tmp))
        imageIndex += 1

        #goalSprite['costumes'].append(mkCostume('level{}'.format(level + 1), imageIndex, fitImage(Image.open(getInput('goal image path'))), tmp))
        print('Goal Image = {}'.format(inData[level]['goal']))
        goalSprite['costumes'].append(mkCostume('level{}'.format(level + 1), imageIndex, fitImage(Image.open(inData[level]['goal'])), tmp))
        imageIndex += 1
        #goalXs.append(int(getInput('goal x')))
        print('Goal pos = ({}, {})'.format(inData[level]['goalX'], inData[level]['goalY']))
        goalXs.append(int(inData[level]['goalX']))
        #goalYs.append(int(getInput('goal y')))
        goalYs.append(int(inData[level]['goalY']))
       
        #imageIndex, wallChunks = genChunks(level + 1, Image.open(getInput('maze walls image path')), imageIndex, tmp, chunkSize)
        print('Maze Image = {}'.format(inData[level]['maze']))
        imageIndex, wallChunks = genChunks(level + 1, Image.open(inData[level]['maze']), imageIndex, tmp, chunkSize)
        wallSprites = combineChunks(wallChunks, wallSprites, level + 1)
 
        level += 1
    

    #finish goal Sprite
    goalSprite['scripts'] = mkGoalScripts(level)
    goalSprite['lists'].append(mkList('starting X', goalXs))
    goalSprite['lists'].append(mkList('starting Y', goalYs))
    prj['children'].append(goalSprite)

    #finish ball Sprite
    ballSprite['scripts'] = mkBallScripts(level)
    prj['children'].append(ballSprite)

    #construct wall sprites
    for i in range(len(wallSprites)):
        prj['children'].append(mkWallSprite(i, i + 2, wallSprites[i], level))

    #finish up Stage
    print('\nWarning: there are {} sprites'.format(len(wallSprites) + 2))
    prj['info']['spriteCount'] = len(wallSprites) + 2
    prj['variables'].append(mkVar('number of levels', level))

    
    #put together project
    if not delWithPerm('{}/project.json'.format(tmp), False):
        print('Failure')
        if not delWithPerm(tmp, False):
            print('Failed to clean up')
        exit()
    else:
        with open('{}/project.json'.format(tmp), 'w') as f:
            json.dump(prj, f, indent=2)
    
    outputName = getInput('project name')
    if not delWithPerm('{}.sb2'.format(outputName)):
        print('Failure')
        if not delWithPerm(tmp, False):
            print('Failed to clean up')
    else:
        zipDir('{}.sb2'.format(outputName), tmp)
        if delWithPerm(tmp, False):
            print('Success')
        else:
            print('Success but failed to clean up')
