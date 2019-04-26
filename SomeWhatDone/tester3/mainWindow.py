from pyglet.gl import *
from pyglet.window import key
from pyglet.window import FPSDisplay
import math
from CarSprite import *
from Line import *
from Track import *
from Grid import *
import numpy as np
import random
from tempfile import TemporaryFile
import sys
WINDOWWIDTH=1280
WINDOWHEIGHT=720

class AI():
    def __init__(self):
        self.maxEpisode = 500000
        self.maxSteps = 2000
        self.learningRate = 0.9
        self.discountRate = 0.5
        self.exploreRate = 1.0
        self.maxExploreRate = 1.0
        self.minExploreRate = 0.1
        self.decayRate= 0.01
        self.actionNum = 4
        self.stateNum = 0
        self.twoToOneD = {}
        self.oneToTwoD = {}
        self.exp_tradeoff=0
        for j in range(12):
            for i in range(24):
                string = str(i)+","+str(j)
                self.twoToOneD[string] = self.stateNum
                self.oneToTwoD[self.stateNum]= string
                self.stateNum+=1
        self.qTable = np.zeros((self.stateNum,self.actionNum))
        self.currentState = self.twoT1([0,0])
        self.episodeCounter = 0
        self.stepCounter = 0
        self.done = False
        self.stopFlag = False
        self.completeCounter=0



        #play
        self.playEpisodeCounter =0
        self.maxPlayEpisode = 100
        self.playStepCounter = 0
        self.maxPlayStep = 300
        self.playCurrentState = self.twoT1([0,0])
        self.stopPlayFlag=False
        self.playDone = False
        self.rewardSum = 0
        self.playCompleteCounter =0
        self.rewards= [] 

        self.actionCounter = 0
        self.actionArray=[None,None,None,None]
        self.stateRepeatCounter = 0
        self.stateRepeatArray=[None,None,None,None]  

    def oneT2(self, number):
        string = self.oneToTwoD[number]
        ijlist = string.split(',')
        i = ijlist[0]
        j = ijlist[1]
        return [i,j]
    def twoT1(self, twoD):
        string = str(twoD[0])+","+str(twoD[1])
        num = self.twoToOneD[string]
        return num
    def actionSample(self):
        return np.random.randint(0,4)
    
    def train(self,window,car):
        
        if self.episodeCounter <self.maxEpisode:
            
            if self.stepCounter < self.maxSteps and self.stopFlag==False:
                #print("here")

                self.exp_tradeoff = random.uniform(0,1)
                if self.exp_tradeoff > self.exploreRate:
                    option="choose"
                    action = np.argmax(self.qTable[self.currentState,:])
                else:
                    option="random"
                    action = self.actionSample()

                repeating = ""
                self.stateRepeatArray[self.stateRepeatCounter%4] = self.currentState
                self.actionArray[self.actionCounter%4] = action
                if self.stepCounter >=4:
                    if self.actionArray[0] ==self.actionArray[2] and self.actionArray[1] ==self.actionArray[3]:
                        if self.stateRepeatArray[0] ==self.stateRepeatArray[2] and self.stateRepeatArray[1] ==self.stateRepeatArray[3]:
                            repeating = "Repeated"
                            while True:
                                action = self.actionSample()
                                if action!=self.actionArray[0] and action!=self.actionArray[1]:
                                    break
                
                newState, reward, self.done = car.newState(action)
                newState = self.twoT1(newState)
                
                #print[self.currentState]
                self.qTable[self.currentState, action] = self.qTable[self.currentState,action] + self.learningRate * (reward + self.discountRate * np.max(self.qTable[newState,:])- self.qTable[self.currentState,action])
                
                self.currentState = newState
                
                if self.done == True:
                    self.stopFlag = True
                    self.completeCounter+=1
                    self.saveFilename = 'auto-save'
                    self.saveFilename = self.saveFilename + str(self.completeCounter) +".txt"
                    np.savetxt(self.saveFilename, self.qTable, fmt='%f')
                    print("saved")
                    #return True
    
                #print [self.qTable[self.currentState,action] + self.learningRate * (reward + self.discountRate * np.max(self.qTable[newState,:])- self.qTable[self.currentState,action])]
                print([self.currentState,newState,action,reward,self.done,option,self.exp_tradeoff,self.exploreRate, repeating])
                self.stepCounter +=1
                
                self.actionCounter +=1
                self.stateRepeatCounter +=1
                if self.actionCounter >=4:
                    self.actionCounter = 0
                if self.stateRepeatCounter >=4:
                    self.stateRepeatCounter = 0
            
            if self.stepCounter ==self.maxSteps-1 or self.stopFlag:
                print("here1")
                self.exploreRate = self.minExploreRate + (self.maxExploreRate - self.minExploreRate)*np.exp(-self.decayRate *self.episodeCounter)        
                self.stepCounter=0
                self.episodeCounter +=1
                window.resetCar()
                self.stopFlag = False
        
        #print(str(self.episodeCounter)+" "+str(self.stepCounter)) 
        
        window.updateES(self.episodeCounter,self.stepCounter,self.completeCounter)

    def play(self,window,car):
        if self.playEpisodeCounter < 1:

            if self.playStepCounter < self.maxPlayStep and self.stopPlayFlag ==False:
                
                action = np.argmax(self.qTable[self.playCurrentState,:])

                playNewState, reward, self.playDone = car.newState(action)
                print([action,playNewState, self.twoT1(playNewState), reward, self.playDone])
                playNewState = self.twoT1(playNewState)
                
                self.rewardSum += reward

                self.playCurrentState = playNewState
                
                if self.playDone == True:
                    self.stopPlayFlag = True
                    self.playCompleteCounter+=1
                    self.rewards.append(self.rewardSum)

                self.playStepCounter +=1
            
            if self.playStepCounter == self.maxPlayStep -1 or self.stopPlayFlag:
                self.playStepCounter = 0
                self.playEpisodeCounter +=1
                window.resetCar()
                self.stopPlayFlag = False
                self.rewardSum = 0
        window.updateES(self.playEpisodeCounter,self.playStepCounter,self.playCompleteCounter)

                

class MyWindow(pyglet.window.Window):
    def __init__(self, *args, **kwargs):
        super(MyWindow,self).__init__(*args, **kwargs)
        #this clear thing affect the background color
        #comment it out to get a black background
        glClearColor(1,1.0,1.0,1)
        self.fps_display = FPSDisplay(self)
        self.car = CarSprite()
        self.key_handler = key.KeyStateHandler()
        self.testTrack= Track([40,60,1200,600],[240,260,800,200])
        self.testGrid = Grid(40,60,1200,600,50)
        self.ai = AI()
        self.train = False
        self.episodeCounter = 0
        self.stepCounter = 0
        self.completeC=0
        self.play = False
            
    def on_draw(self):
        glClear(GL_COLOR_BUFFER_BIT)
        self.fps_display.draw()
        self.testGrid.draw()
        self.testTrack.draw()
        self.car.draw()
        self.centerLabel = pyglet.text.Label()
        self.centerLabel.draw()
        self.centerLabel = pyglet.text.Label(("KeepTrack 200 Episode = " + str(self.episodeCounter)+ " , Step = " + str(self.stepCounter)+ " , Complete = " + str(self.completeC)),
                font_name='Times New Roman',                      
                font_size=15,
                x= 400, y=20,
                color=(0, 0, 255, 255))
        self.centerLabel.draw()
        
    def on_key_press(self, symbol,modifiers):
        if symbol == key.UP:
            #print(self.car.goStraight())
            #print(self.car.newState(0))
            #self.car.goStraight()
            self.car.newState(0)
        elif symbol == key.DOWN:
            #self.car.goReverse()
            #print(self.car.goReverse())
            self.car.newState(3)
        elif symbol == key.LEFT:
            #print(self.car.turnLeft())
            #self.car.turnLeft()
            self.car.newState(1)
        elif symbol == key.RIGHT:
            self.car.newState(2)
            #print(self.car.turnRight())
            #self.car.turnRight()
        elif symbol == key.ESCAPE:
            pyglet.app.exit()
        elif symbol == key.SPACE:
            #outfile = TemporaryFile()
            #np.save(outfile,self.ai.qTable)
            np.savetxt('test1.txt', self.ai.qTable, fmt='%f')
            print("saved")
        
        elif symbol == key.ENTER:
            self.train = True
            self.play = False
        
        elif symbol == key.BACKSPACE:
            self.play = True
            self.train = False
        
        elif symbol == key._1:
            tempA = np.loadtxt('auto-save1.txt2.txt3.txt', dtype =float)
            self.ai.qTable = tempA
            print(self.ai.qTable)
    
    #reset car env
    def resetCar(self):
        self.car = CarSprite()

    #check for points
    #check for complete
    #done when checkpoint is TRUE
    #then reset
    
    def update(self, dt):
        #print(self.ai.twoT1(self.car.currentState()))
        #print(self.ai.oneT2(self.ai.twoT1(self.car.currentState())))
        if self.train:
            self.ai.train(self,self.car)
            #print(str(sum(self.ai.rewards)/self.ai.playEpisodeCounter))
        if self.play or len(sys.argv)>1:
            name = str(sys.argv[1]) + ".txt"
            tempA = np.loadtxt(name, dtype =float)
            self.ai.qTable = tempA
            self.ai.play(self,self.car)
        
    def updateES(self,episode,step,complete):
        self.episodeCounter = episode
        self.stepCounter = step
        self.completeC = complete
            
if __name__ == "__main__":
    window = MyWindow(WINDOWWIDTH,WINDOWHEIGHT, "DRIFT AI", resizable=True, vsync =True)
    window.push_handlers(window.key_handler)
    pyglet.clock.schedule_interval(window.update,1/100.0)
    pyglet.app.run()