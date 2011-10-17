import sys,os
import pygame
from pygame.locals import *
import math
import operator
import config
import random
import weakref

# 257, 409

class QuitGameException(Exception): pass

#-----------------------------------------------------------------------------	

def linearPath(t, points):
	"""Takes a time value and a list of (time, number) pairs.
	Finds the appropriate two points the time value falls between,
	and interpolates linearly between them accordingly.
	"""
	assert len(points) > 1
	last = None
	for n in range(0,len(points)-1):
		a = points[n]
		b = points[n+1]
		if t < a[0]:
			return a[1]
		elif t >= a[0] and t < b[0]:
			if a[1] == b[1]:
				return a[1]
			# TODO: Interp
			assert b[0] != a[0]
			r = (t-a[0])/(b[0]-a[0])
			return a[1]*(1.0-r) + b[1]*r
		else:
			last = b
	return last[1]	

#-----------------------------------------------------------------------------

class Node:
	def __init__(self, parent, game=None, paused=False, visible=True, state=0, children=[], zOrder=0):
		if parent == None:
			assert game != None, "Cannot use parent=None unless you supply a game"
			self.parent = None
			self.game = game
		else:
			assert isinstance(parent, Node), "Parent must be a node"
			assert game == None, "Cannot supply a game unless parent=None"
			self.parent = parent
			self.game = parent.game
		self.kill = False
		self.result = 0
		self.paused = paused
		self.visible = visible
		self.state = state
		self.children = children[:]
		self.zOrder = zOrder
		self.birthTicks = pygame.time.get_ticks()
		self.time = 0
		
	def addChild(self, c):
		assert isinstance(c, Node), "child to add must be a Node"
		assert c != self, "Cannot be a child of yourself!"
		self.children.append(c)
		self.children.sort(lambda a,b: cmp(a.zOrder,b.zOrder))
			
	def generalUpdate(self):
		self.time = (pygame.time.get_ticks() - self.birthTicks)/1000.0
		
		if not self.paused:
			self.update()
		
		needKill = False
		for child in self.children:
			child.generalUpdate()
			if child.kill:
				child.unlink()
				needKill = True
				
		if needKill:
			self.killed = [x for x in self.children if x.kill]
			self.children = [x for x in self.children if not x.kill]
			
			# TODO: This is kind of bad, it gives you unlinked children to work on
			for k in self.killed:
				self.onChildKilled(k)
				
	def unlink(self):
		for c in self.children:
			c.unlink()
		self.parent = None
		self.game = None
				
	def enterState(self, state):
		oldstate = self.state
		self.state = state
		self.onEnterState(state, oldstate)
	
	def onEnterState(self, state, oldstate): pass
				
	def onChildKilled(self, child): pass	
			
	def update(self): pass
	
	def generalRender(self):
		if self.visible:
			self.render()
			
			for child in self.children:
				child.generalRender()
				
	def render(self): pass

#-----------------------------------------------------------------------------	

class Sprite(Node):
	def __init__(self, parent, image, x=0, y=0, centered=False, **kwargs):
		#assert isinstance(overlay, Overlay), "overlay must be an Overlay"
		Node.__init__(self, parent, **kwargs)
		self.x = x
		self.y = y
		self.centered = centered
		self.frame = 0
		
		if operator.isSequenceType(image) and not isinstance(image, str):
			assert len(image) > 0
			self.images = [self._convertImageListItem(x) for x in image]
		else:
			self.images = [self._convertImageListItem(image)]
				
		self.imageSize = self.images[0].get_size()
		
	def _convertImageListItem(self, image):
		assert isinstance(image, pygame.Surface) or isinstance(image, str), \
				"image must be a string or a Surface"
		if isinstance(image, str):
			return self.game.loadImage(image)
		else:
			return image
		
	def update(self): pass
	
	def render(self):
		x,y = self.getTopLeft()
		assert self.frame < len(self.images) and self.frame >= 0
		self.game.screen.blit(self.images[self.frame], (x,y))
		
	def getTopLeft(self):
		x,y = self.x, self.y
		if self.centered:
			x -= self.imageSize[0]/2
			y -= self.imageSize[1]/2
		return x,y

#-----------------------------------------------------------------------------	

class Text(Node):
	def __init__(self, parent, font, text='', x=0, y=0, **kwargs):
		#assert isinstance(font, pygame.Font), "font must be a Pygame font"
		Node.__init__(self, parent, **kwargs)
		self.font = font
		self.text = text
		self.x = x
		self.y = y
		self.surf = None
		
	def setText(self, text):
		if text == self.text:
			return
		if self.surf:
			self.surf = None
		self.text = text
		
	def render(self):
		if not self.surf:
			self.surf = self.font.render(self.text, True, (255,255,255,255), (0,0,0,255))
		self.game.screen.blit(self.surf, (self.x,self.y))

#-----------------------------------------------------------------------------		

class ScrollyThing(Sprite):
	def __init__(self, parent, image, points, **kwargs):
		Sprite.__init__(self, parent, os.path.join('intro',image), centered=True, **kwargs)
		self.points = points
		
	def update(self):
		self.x = 640/2
		self.y = linearPath(self.time, self.points)
		self.visible = (self.time >= self.points[0][0] and
						self.time <= self.points[-1][0])
					
class IntroTextOverlay(Node):
	def __init__(self, parent, **kwargs):
		Node.__init__(self, parent, **kwargs)
		
		self.sprites = []
		srhPoints = [(0,480+100), (13.24, 240), (18.71, 240), (18.71+13.24, -100)]
		self.addChild(ScrollyThing(self, "srh.png", srhPoints))
		
		off = 20.8
		_1w1bPoints = [(x[0]+off, x[1]) for x in srhPoints]
		self.addChild(ScrollyThing(self, "1w1b.png", _1w1bPoints))
		
		off = 20.8*2-0.5
		instructionsPoints = [(x[0]+off, x[1]) for x in srhPoints]
		self.addChild(ScrollyThing(self, "instructions.png", instructionsPoints))
		
		off = 20.8*3+1.0
		instructions2Points = [(x[0]+off, x[1]) for x in srhPoints]
		instructions2Points.pop(-1)
		instructions2Points[-1] = (60+26.75, 240)
		self.addChild(ScrollyThing(self, "instructions2.png", instructions2Points))
		
	def update(self):
		if self.time > 60+30:
			self.kill = True
		
#-----------------------------------------------------------------------------	

class CornerThing(Sprite):
	def __init__(self, parent, image, pos, **kwargs):
		Sprite.__init__(self, parent, image, **kwargs)
		self.pos = pos
		self.startX = [-30, 640][pos[0]]
		self.startY = [-30, 480][pos[1]]
		self.endX = [0, 640-30][pos[0]]
		self.endY = [0, 480-30][pos[1]]
		self.x, self.y = self.startX, self.startY

class CornerOverlay(Node):
	def __init__(self, parent, **kwargs):
		Node.__init__(self, parent, **kwargs)
		
		self.addChild(CornerThing(self, "corner-top-left.png", (0,0)))
		self.addChild(CornerThing(self, "corner-top-right.png", (1,0)))
		self.addChild(CornerThing(self, "corner-bottom-left.png", (0,1)))
		self.addChild(CornerThing(self, "corner-bottom-right.png", (1,1)))
		
	def update(self):
		for n in range(len(self.children)):
			spr = self.children[n]
			if n <= self.time and n+1 > self.time:
				r = self.time-n
				spr.x = spr.startX*(1-r) + spr.endX*r
				spr.y = spr.startY*(1-r) + spr.endY*r
			elif n+1 <= self.time:
				spr.x, spr.y = spr.endX, spr.endY
		

#-----------------------------------------------------------------------------

class PooSignGuy(Sprite):
	def __init__(self, parent, signName, **kwargs):
		frames = [os.path.join("poo", "poo-%d.png" % x) for x in range(4)]
		Sprite.__init__(self, parent, frames)
		self.sign = None
		self.changeSign(signName)
		self.forceFrame = -1
		self.subtractTime = 0
		
	def changeSign(self, signName):
		if self.sign != None:
			self.sign.kill = True
		self.sign = Sprite(self, os.path.join("sign",signName))
		self.sign.zOrder = 10
		self.addChild(self.sign)
		self._fixSign()		
		
	def _fixSign(self):
		self.sign.visible = (self.frame < 2)
		left,top = self.getTopLeft()
		self.sign.x = left + 19
		self.sign.y = top + [5,7][self.frame == 1]
		
	def update(self):
		if self.forceFrame < 0:
			t = self.time - self.subtractTime
			x = math.fmod(t, 1.0)
			if x < 0.5:
				self.frame = 0
			else:
				self.frame = 1
		else:
			self.frame = self.forceFrame
		self._fixSign()

class TitleOverlay(Node):
	def __init__(self, parent, **kwargs):
		Node.__init__(self, parent, **kwargs)
		self.poo = PooSignGuy(self, "press-space.png")
		self.poo.visible = False
		self.poo.centered = True
		self.poo.x, self.poo.y = (320, 350)
		self.title = Sprite(self, "title.png")
		self.addChild(self.title)
		self.addChild(self.poo)
		self.title.y = -480
		self.tv = 0
		self.titleStopped = False
		
	def update(self):
		# Bounce the title
		deltat = self.game.deltat
		#print self.title.y
		if not self.titleStopped:
			self.title.y += self.tv * deltat
			self.tv += 3000.0*deltat
			if self.title.y > 0:
				self.title.y = 0
				if self.tv > 0:
					newmag = self.tv*0.5 - 100
					self.tv = -max(newmag, 0)
					if abs(self.tv) < 5.0:
						self.titleStopped = True
		
		if self.time > 3.25:
			self.poo.visible = True

#-----------------------------------------------------------------------------	

class ImageRevealer(Node):	
	def __init__(self, parent, name, **kwargs):
		Node.__init__(self, parent, **kwargs)
		self.name = name
		# State of revealing we're doing.
		# Stage 0 = Question marks -> blurry
		# Stage 1 = blurry -> less blurry
		# Stage 2 = less blurry -> clear
		self.stage = 0
		self.baseImage = None
		self.covers = []
		self.revealing = False
		self.revealTimer = 0
		self.revealInterval = 0.25
		self.order = []
		self.revealCount = 0
		
		# The images we're using (keep them alive the entire lifetime of the image revealer)
		self.clearImage = self.game.loadImage(os.path.join("questions",self.name+".jpg"))
		self.lessBlurryImage = self.game.loadImage(os.path.join("questions",self.name+"-lessblurry.jpg"))
		self.blurryImage = self.game.loadImage(os.path.join("questions",self.name+"-blurry.jpg"))
		
		self._doStage(0, self.blurryImage)
	
	# TODO: This is probably not necessary
	def unlink(self):
		Node.unlink(self)
		self.clearImage = None
		self.lessBlurryImage = None
		self.blurryImage = None
		
	def update(self):
		if self.revealing:
			self.revealTimer += self.game.deltat
			while self.revealTimer > self.revealInterval:
				self._revealNextSquare()
				self.revealTimer -= self.revealInterval
				
	def _revealNextSquare(self):
		if len(self.covers) > 0:
			cover = self.covers.pop(0)
			cover.kill = True
			#print "Revealed square %d" % self.revealCount
			self.revealCount += 1
		else:
			self._nextStage()
			
	def _nextStage(self):
		if  self.stage == 0:
			#print "Entering second stage!"
			self._doStage(1, self.lessBlurryImage, self.blurryImage)
		elif self.stage == 1:
			#print "Entering third stage!"
			self._doStage(2, self.clearImage, self.lessBlurryImage)
		else:
			self.revealing = False
		
	def _doStage(self, stageNum, baseImage, coverImage=None):
		self.stage = stageNum
		self._setBaseImage(baseImage)		
		
		for x in self.covers:
			x.kill = True
		self.covers = []
		
		if coverImage != None:
			if isinstance(coverImage, str):
				coverImageObj = self.game.loadImage(coverImage)
			else:
				coverImageObj = coverImage
		
		for x in range(8):
			for y in range(6):
				thisCoverImage = 'cover.png'
				if coverImage != None:
					surf = pygame.Surface((50,50)).convert() # TODO: Do we have to convert or not?
					surf.blit(coverImageObj, (0,0), pygame.Rect((x*50, y*50, (x+1)*50, (y+1)*50)))
					thisCoverImage = surf
				cover = Sprite(self, thisCoverImage)
				cover.x = (640/2)-(400/2)+x*50
				cover.y = (480/2)-(300/2)+y*50
				cover.z = 5
				self.addChild(cover)
				self.covers.append(cover)
				
		random.shuffle(self.covers)
			
	def _setBaseImage(self, baseImage):
		if self.baseImage != None:
			self.baseImage.kill = True
		self.baseImage = Sprite(self, baseImage, centered=True)
		self.baseImage.x, self.baseImage.y = (640/2, 480/2)
		self.baseImage.centered = True
		self.addChild(self.baseImage)
		
	def revealImage(self):
		print "Revealing image!"
		self.revealIndex = 0
		#self._setBaseImage(os.path.join("questions", self.name+".jpg"))
		order = [x for x in self.covers if not x.kill]
		random.shuffle(order)
		t=0
		for o in order:
			print "%s %d -> %d" % (repr(o), o.index, t)
			o.index = t
			t += 1
			

#-----------------------------------------------------------------------------

STATE_READY = 0 	# Poo sign guy says "Ready..."
STATE_SET = 1		# Poo sign guy says "Set..."
STATE_GO = 2		# Poo sign guy says "Go!!", you can start making a choice now
STATE_CHOOSING = 3 	# Choice is being made, fixed amount of time until it's done
STATE_CHOSEN = 4	# Choice is final
STATE_LIMBO = 5		# Dead, basically.
			
class QuestionOverlay(Node):
	def __init__(self, parent, **kwargs):
		Node.__init__(self, parent, **kwargs)
			
		allquestions = [("cockpit", False),
						  ("wedding", False),
						  ("kittens", False),
						  ("factory", False),
						  ("classroom", False),
						  ("car", False),
						  ("dojo", False),
						  ("graduation", False),
						  
						  ("meiji", True),
						  ("outhouse", True),
						  ("japan", True),
						  ("china", True),
						  ("forest", True),
						  ("lavatory", True),
						  ("residential", True),
						  ("ecuador", True)]
		self.questions = allquestions
		random.shuffle(self.questions)
		self.questions = self.questions[:10] # TODO: 10

		# This gets filled in later
		self.revealer = None	
		
		self.correctAnswer = False # True = yes, False = no
		
		# The background, which contains everything but the 
		# poo guy, the question image, the stats readouts, and the glove cursor
		self.bg = Sprite(self, "question-bg.png")
		self.bg.zOrder = -10
		self.addChild(self.bg)
		
		# The little poo guy with the sign.
		# He flips it from "Ready", "Set", to "Go!!"
		# Until he hits Go he isn't bouncing up and down at all.
		self.poo = PooSignGuy(self, "ready.png")
		self.poo.x = 640/2-400/2
		self.poo.y = 480/2-300/2 - self.poo.imageSize[1] - 5
		self.poo.forceFrame = 0
		self.addChild(self.poo)
		self.state = STATE_READY
		
		# The gloves hand cursor sprite, used for selections
		self.cursor = Sprite(self, "glove.png")
		self.cursor.x = 257
		self.cursor.y = 409
		self.addChild(self.cursor)
		
		self.font = pygame.font.Font(os.path.join('misc','arial.ttf'), 12)
		
		self.scoreText = Text(self, self.font, "1234", x=22, y=151, zOrder=100)
		self.addChild(self.scoreText)
		
		self.timeText = Text(self, self.font, "1234", x=22, y=151+42, zOrder=100)
		self.addChild(self.timeText)
		
		self.valueText = Text(self, self.font, "1234", x=22, y=151+42*2, zOrder=100)
		self.addChild(self.valueText)
		
		self.progressText = Text(self, self.font, "1234", x=22, y=151+42*3, zOrder=100)
		self.addChild(self.progressText)
		
		self.accuracyText = Text(self, self.font, "1234", x=22, y=151+42*4, zOrder=100)
		self.addChild(self.accuracyText)
		
		self.flasher = Sprite(self, "blackout.png")
		self.flasher.visible = False
		self.addChild(self.flasher)
		
		self.rotateSign = 0
		self.signChanged = False
		self.pendingSign = ""
		
		# Current stats!
		self.score = 0
		self.totalQuestions = len(self.questions)
		self.currQuestion = 0 # Will be incremented when we call _nextQuestion
		self.right = 0
		self.answered = 0
		
		# Used for showing score and updating it when you win/lose
		self.showScore = 0
		self.scoreRollSign = 0
	
		self._nextQuestion()
				
	def _nextQuestion(self):
		if len(self.questions) == 0:
			self.state = STATE_LIMBO
			self.kill = True
		else:
			q = self.questions.pop(0)
			self._startQuestion(q[0], q[1])
			
	def _updateValue(self):
		assert self.state <= STATE_GO
		t = self.currentTime
		t = min(40,t)
		t = max(0, t)
		t /= 40.0
		t = 1-t
		t *= 1000
		self.currentValue = round(t + 200)
			
	def _startQuestion(self, name, answer):
		if self.revealer:
			self.revealer.kill = True
			
		self.revealer = ImageRevealer(self, name)
		self.addChild(self.revealer)	
		
		self.showScore = self.score
		self.name = name
		self.correctAnswer = answer
		self.currentTime = 0
		self.chooseTime = 0
		self.selection = 0
		self.padTime = 0
		self.warmupTime = 0
		
		self.currQuestion += 1
		
		self._changeAndRotateSign("ready.png")		
		
		self.state = STATE_READY
		self._updateCursorPos()
		self._updateValue()
		
	def _changeAndRotateSign(self, sign):
		self.rotateSign = 1.0
		self.signChanged = False
		self.pendingSign = sign
		
	def _updateCursorPos(self):
		# Adjust cursor position depending on the current choice
		self.cursor.y = 409 + self.selection*13
		
	def onSpacePressed(self):
		# TODO: Blah!
		if self.state == STATE_GO or self.state == STATE_CHOOSING:
			if self.state != STATE_CHOOSING:
				self._changeAndRotateSign('choosing.png')
				self.state = STATE_CHOOSING
				self.revealer.revealing = False
				
			self.selection += 1
			if self.selection > 2:
				self.selection = 1
			self.chooseTime = 2.0
		self._updateCursorPos()
	
	def _updateRotatingSign(self):
		self.poo.forceFrame = 0
		if self.rotateSign > 0:
			t = self.rotateSign
			if t > 0.8 and t < 1:
				self.poo.forceFrame = 2
			if t > 0.866 and t < 0.933:
				self.poo.forceFrame = 3	
			if t <= 0.8 and not self.signChanged:
				self.poo.changeSign(self.pendingSign)
				self.signChanged = True
			self.rotateSign -= self.game.deltat
		
	def _rightAnswer(self):
		self._changeAndRotateSign('great-job.png')
		self.answered += 1
		self.right += 1
		self.showScore = self.score
		self.scoreRollSign = +1
		self.score += self.currentValue
		self.awardedValue = self.currentValue
		self._transitionNext()
						
	def _wrongAnswer(self, timeUp=False):
		self._changeAndRotateSign(['sorry.png', 'time-up.png'][timeUp])
		self.answered += 1
		self.showScore = self.score
		self.scoreRollSign = -1
		self.score -= self.currentValue
		self.awardedValue = self.currentValue
		self._transitionNext()
		
	def _pass(self):
		assert 0 # Don't call
		self._changeAndRotateSign('pass.png')
		self._transitionNext()
		
	def _transitionNext(self):
		self.state = STATE_CHOSEN
		self.flasher.visible = True
		self.flasher.x = 280
		self.flasher.y = 423 + [0,13][self.correctAnswer == False]
		self.revealer.revealing = True
		self.revealer.revealTimer = 0 # hack hack
		self.revealer.revealInterval = 0.25/32.0
		
	def update(self):
	
		self.scoreText.setText("%d points" % self.showScore)
		self.timeText.setText("%2.2f sec" % self.currentTime)
		self.valueText.setText("%d points" % self.currentValue)
		self.progressText.setText("%d/%d" % (self.currQuestion, self.totalQuestions))
		if self.answered != 0:
			percent = int(round(100.0*self.right/self.answered))
			self.accuracyText.setText("%d%% (%d/%d)" % (percent, self.right, self.answered))
		else:
			self.accuracyText.setText("0% (0/0)")
		
		if self.state < STATE_GO:
			assert (self.state == STATE_READY or
					self.state == STATE_SET or
					self.state == STATE_GO), "Unknown state"
			# Displaying either "Ready" or "Set" sign.
			self._updateRotatingSign()
			
			self.warmupTime += self.game.deltat
			
			if self.warmupTime >= 1.0 and self.state != STATE_SET:
				self.state = STATE_SET
				self._changeAndRotateSign("set.png")
			elif self.warmupTime >= 2.0:
				self.state = STATE_GO
				self._changeAndRotateSign("go.png")
				self.poo.subtractTime = self.poo.time
				self.poo.forceFrame = -1
				self.revealer.revealing = True
		elif self.state == STATE_GO:
			self.currentTime += self.game.deltat
			self._updateValue()
			self._updateRotatingSign()
			if self.rotateSign < 0.5:
				self.poo.forceFrame = -1
			
			# This length depends on the number of grid squares,
			# number of layers, and revealing speed...
			# 8*6*3*0.25 = 36.0, padded to 40
			if self.currentTime > 40.0:
				self._wrongAnswer(True)
				
			# Nothing :P
		elif self.state == STATE_CHOOSING:
			# Currently in the process of choosing -- the image won't
			# be revealed any more
			
			self._updateRotatingSign()	
					
			self.chooseTime -= self.game.deltat
			if self.chooseTime <= 0:
				print "Choice is complete"
				# TODO: Better handling here
				if self.selection == 0:
					# TODO: Um, I don't think you can even get here :)
					#self._pass()
					assert 0
				elif self.selection == 1:
					if self.correctAnswer == True:
						self._rightAnswer()
					else:
						self._wrongAnswer()			
				elif self.selection == 2:
					if self.correctAnswer == False:
						self._rightAnswer()
					else:
						self._wrongAnswer()	
				assert self.state != STATE_CHOOSING, "Should have changed states"
				#elif self.selection == 3:
				#	self._pass()						
		elif self.state == STATE_CHOSEN:
			# An answer has been chosen!
			
			if self.currentTime > 0:
				modifyAmt = self.game.deltat * 12.0
				if self.currentTime > modifyAmt:
					self.currentTime -= modifyAmt
				else:
					self.currentTime = 0
			
			if self.currentValue != 0:
				modifyAmt = int(round(self.game.deltat * 700))
				if self.currentValue >= modifyAmt:
					self.showScore += modifyAmt * self.scoreRollSign
					self.currentValue -= modifyAmt
				else:
					self.showScore += self.currentValue * self.scoreRollSign
					self.currentValue = 0
					assert self.showScore == self.score, "Should have ended up with the correct score"
			
			if self.padTime < 3.0:
				self.flasher.visible = math.fmod(self.padTime*3, 1.0) < 0.5
			else:
				self.flasher.visible = False
			
			self.padTime += self.game.deltat
			if self.padTime > 5.0:
				self.flasher.visible = False
				self._nextQuestion()
				assert self.state != STATE_CHOSEN, "Should have changed states"
			
			# TODO: Flash the correct answer
			self._updateRotatingSign()	
		elif self.state == STATE_LIMBO:
			pass
		else:
			assert 0, "Don't know this state!"

#-----------------------------------------------------------------------------

class GameOverOverlay(Node):
	def __init__(self, parent, score, **kwargs):
		Node.__init__(self, parent, **kwargs)
		self.score = score
		self.bg = Sprite(self, "gameover-bg.png")
		self.addChild(self.bg)
		
		# TODO: "Game over" sign
		self.poo = PooSignGuy(self, "game-over.png")
		self.poo.centered = True
		self.poo.x, self.poo.y = (320, 240)
		self.addChild(self.poo)
		
		# TODO: Score
		font = pygame.font.Font(os.path.join("misc","arial.ttf"), 13)
		#self.score = 1234
		self.scoreText = Text(self, font, "%d" % self.score)
		self.scoreText.x = 348-5
		self.scoreText.y = 284-4
		self.addChild(self.scoreText)
		
#-----------------------------------------------------------------------------	

STATE_ALIGN = 0
STATE_INTRO = 1
STATE_TITLE = 2
STATE_GAME = 3
STATE_GAMEOVER = 4

class CoreControl(Node):
	def __init__(self, parent, **kwargs):
		Node.__init__(self, parent, **kwargs)
		self.state = STATE_ALIGN
		
		self.lastScore = 0
		#self.titleOverlay = None
		#self.introOverlay = None
		#self.gameOverlay = None
		self.cornerOverlay = CornerOverlay(self, zOrder=10)
		self.currScreen = None
		self.addChild(self.cornerOverlay)
		
		self.enterState(STATE_ALIGN)
		#self.enterState(STATE_GAME)
		#self.enterState(STATE_GAMEOVER)
		
	def update(self):
		if self.cornerOverlay.time > 4 and self.state == STATE_ALIGN:
			self.enterState(STATE_INTRO)
		
	def changeScreen(self, screen):
		if self.currScreen != None:
			self.currScreen.kill = True
		self.currScreen = screen
		self.addChild(self.currScreen)
			
	def onEnterState(self, state, oldstate):
		if state == STATE_ALIGN:
			self.game.startMusic("static.ogg")
		elif state == STATE_INTRO:
			self.changeScreen(IntroTextOverlay(self))
			self.game.startMusic("2001_nointro.ogg")
		elif state == STATE_TITLE:
			self.changeScreen(TitleOverlay(self))
			self.game.startMusic("bennyhill.ogg", True)
		elif state == STATE_GAME:
			self.changeScreen(QuestionOverlay(self))
			self.game.startMusic("bennyhill.ogg", True)
		elif state == STATE_GAMEOVER:
			self.changeScreen(GameOverOverlay(self, self.lastScore))
			self.game.startMusic("bennyhill.ogg", True)
		else:
			assert 0, "Don't know this state"
			
	def onChildKilled(self, child):
		if self.state == STATE_INTRO and child == self.currScreen:
			self.enterState(STATE_TITLE)
		if self.state == STATE_GAME and child == self.currScreen:
			self.lastScore = self.currScreen.score
			self.enterState(STATE_GAMEOVER)
			
	def onSpacePressed(self):
		if self.state == STATE_INTRO:
			self.enterState(STATE_TITLE)
		elif self.state == STATE_TITLE:
			self.enterState(STATE_GAME)
		elif self.state == STATE_GAME:
			self.currScreen.onSpacePressed()
		elif self.state == STATE_GAMEOVER:
			self.enterState(STATE_TITLE)

#-----------------------------------------------------------------------------	

#MUSIC_DONE_EVENT = USEREVENT+5

class Game:
	def __init__(self):
		self.ran = False
		self.currentMusic = None
		self.imageCache = {}
		
	def run(self):
		try:
			self._run()
		except QuitGameException:
			pass
		
	def _run(self):
		assert not self.ran
		self.ran = True
		pygame.init()
		self.screen = pygame.display.set_mode((640, 480), [0,FULLSCREEN][config.fullscreen])
		pygame.display.set_caption("SHilbert's 1W1B Entry")
		pygame.mouse.set_visible(0)
				
		self.clock = pygame.time.Clock()
				
		
		self._cacheStuff()
		self.core = CoreControl(None, game=self)
		self.clock.tick()
		while 1:
			self._update()
			
	def _update(self):
		self.clock.tick(60)
		self.deltat = self.clock.get_time() / 1000.0
		if self.deltat > 0.1:
			self.deltat = 0.1
		
		self._handleEvents()
		
		self.core.generalUpdate()
		if self.core.kill:
			raise QuitGameException()
			
		self.screen.fill((0,0,0))
		self.core.generalRender()
			
		pygame.display.flip()
		
	def _handleEvents(self):
		for event in pygame.event.get():
			if event.type == QUIT:
				raise QuitGameException()
			elif event.type == KEYDOWN:
				if event.key == K_ESCAPE:
					# TODO: For the intro, go to the title;
					#		for the title, quit;
					#		from the game, go to the title also
					raise QuitGameException()
				elif event.key == K_SPACE:
					self.core.onSpacePressed()
			# TODO: Whatever else events we need to handle
							
	def loadImage(self, path, cache=False):
		path = os.path.join("images", path)
		img = self.imageCache.get(path)
		if img != None:
			return img
		print "Loading %s" % path
		img = pygame.image.load(path).convert()
		if cache:
			self.imageCache[path] = img
		return img
		
	def _cacheStuff(self):
		print "*** Begin batch load"
		images = ["corner-bottom-left.png",
				 "corner-bottom-right.png",
				 "corner-top-left.png",
				 "corner-top-right.png",
				 "cover.png",
				 "glove.png",
				 "question-bg.png",
				 "title.png",
				 "blackout.png",
				 "poo/poo-0.png",
				 "poo/poo-1.png",
				 "poo/poo-2.png",
				 "poo/poo-3.png",
				 "sign/press-space.png",
				 "sign/ready.png",
				 "sign/set.png",
				 "sign/go.png",
				 "sign/choosing.png",
				 "sign/great-job.png",
				 "sign/sorry.png",
				 "sign/pass.png",
				 "sign/time-up.png",
				 "sign/game-over.png",
				 "intro/srh.png",
				 "intro/1w1b.png",
				 "intro/instructions.png",
				 "intro/instructions2.png"]
		for image in images:
			parts = image.split("/")
			# Don't use weakrefs for these!
			self.loadImage(apply(os.path.join, parts), cache=True)
		print "*** End batch load"
		
	# Note: playing music looks like it's Python soaking up memory,
	# 		but it's just SDL's music player streaming the music
	#		into memory, I believe.
	# Note: Theoretically, you could request to play something looped,
	#		but if it was already playing as non-looped then it would
	#		not loop once that got to the end (because it just returns
	#		if it thinks we're already playing something.) Also, this
	#		means re-starting a stopped music immediately is going to 
	#		not work.
	def startMusic(self, path, loop=False):
		path = os.path.join("music",path)
		# If we're already playing the right music, don't stop it!
		if path == self.currentMusic:
			return
					
		try:
			pygame.mixer.music.load(path)
			#pygame.mixer.music.set_endevent(MUSIC_DONE_EVENT)
			pygame.mixer.music.play([0,-1][loop])
			print "Playing %s" % path
		except:
			print "Couldn't play %s (mixer might not have loaded properly)" % path
		
		self.currentMusic = path
			
if __name__ == '__main__':
	try:
		game = Game()
		game.run()	
	except:
		import traceback as tb
		tb.print_exc()
		f = file("exception.txt", "w")
		f.write(tb.format_exc())
		f.close()
