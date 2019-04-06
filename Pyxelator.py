from PIL import Image, ImageDraw
from operator import itemgetter
from random import randint, random
import numpy
import argparse
import logging
logger = logging.getLogger()


# global variables
palette = []                # colours of the input image
whiteBackground = True      # boolean for background colour
numGenerationsTotal = 4000  # number of total generations
mutationFactor = 600        # 1/mutationFactor = probability of mutation
populationSize = 100        # size of the population
dotSize = 11                # size of the dots


# The gene of the individuals. It has a colour and a position.
class Dot:
    def __init__(self, x, y, colour):
        self.colour = colour  # (red, green, blue)
        self.x = x          
        self.y = y       

    # The colour of the Dot mutates to another random colour from the palette.
    def mutate(self):
        global palette
        self.colour = palette[randint(0,len(palette)-1)]  

# An individual of the population, a drawn image that tries to replicate the input image.
class Replica:  
    def __init__(self):
        self.dots = []
        # A Replica contains 2,116 dots (46 * 46, because of 512 / 11 = 46).

    # Returns the array of Dots.
    def getDots(self):
        return self.dots

    # Generates and returns an Image with the Dots painted in it.
    def print(self):
        global dotSize
        global whiteBackground
        if whiteBackground:
            resultImage = Image.new("RGB", (512,512), (255, 255, 255))
        else:
            resultImage = Image.new("RGB", (512,512), (0, 0, 0))
        canvas = ImageDraw.Draw(resultImage)
        for dot in self.dots:
            canvas.ellipse([dot.x, dot.y, dot.x+(dotSize-1),dot.y+(dotSize-1)], fill=dot.colour)
        
        return resultImage
        
    # Generates the Dots with a random colour of the palette.
    def generateRandom(self):
        global palette
        global dotSize
        i = 3
        while i < 506:
            j = 3
            while j < 506:
                self.dots.append(Dot(x=i, y=j, colour=palette[randint(0,len(palette)-1)]))
                j += dotSize
            i += dotSize
        return self

    # Scores itself by converting itself and the input image to arrays
    #   the score indicates how different they are (0% very similar, 100% completely different)
    #       from https://www.raspberrypi.org/forums/viewtopic.php?t=195181.
    def getFitnessScore(self, inputImage):
        selfPrinted = self.print()
        arraySelf = numpy.array(selfPrinted).astype(numpy.int)
        arrayInput = numpy.array(inputImage).astype(numpy.int)
        return (numpy.abs(arraySelf-arrayInput).sum() / 255.0 * 100) / arrayInput.size

    # The Dots are filled with the ones of each individual with a probability of 50%.
    def crossover(self, firstIndividual, secondIndividual):
        firstDots = firstIndividual[0].getDots()
        secondDots = secondIndividual[0].getDots()
        for i in range(0, len(firstDots)):
            if random() < 0.5:
                self.dots.append(Dot(firstDots[i].x, firstDots[i].y, firstDots[i].colour))
            else:
                self.dots.append(Dot(secondDots[i].x, secondDots[i].y, secondDots[i].colour))

    # The Dots are mutated depending on a probability.
    def mutate(self):
        global mutationFactor
        for dot in self.dots:
            if randint(0,mutationFactor) == 1:
                dot.mutate()
                
# All Replicas of the input image.
class Population:
    def __init__(self, size, inputImage):
        self.size = size
        self.population = []
        self.inputImage = inputImage
        self.generateFirstPopulation()

    # Generates the first population completely random.
    def generateFirstPopulation(self):
        for i in range(0, self.size-1):
            replica = Replica().generateRandom()
            self.population.append((replica,replica.getFitnessScore(self.inputImage)))
        self.sort()

    # Generates next generation by selecting the best half of the population
    #   and doing crossover between them and mutating the new individual.
    def generateNextGeneration(self):        
        half = (len(self.population) + 1) / 2
        newPopulation = self.population[:int(half)]

        for i in range(0, int(half)):
            newIndividual = Replica()
            newIndividual.crossover(newPopulation[i], newPopulation[randint(0, int(half)-1)])
            newIndividual.mutate()
            newPopulation.append((newIndividual,newIndividual.getFitnessScore(self.inputImage)))

        self.population = newPopulation
        self.sort()

    # Returns the first Replica, as it is sorted, it is always the best one.
    def getFirst(self):
        return self.population[0][0]

    # Returns the first score, as it is sorted, it is always the best one.
    def getFirstScore(self):
        return self.population[0][1]

    # Prints the population's best's score fitness.
    def printBest(self):
        print(self.population[0][1])

    # Sorts the population by its fitness score.
    def sort(self):
        self.population.sort(key=lambda tup: tup[1])

# Finds the HSV's value of the colour sent as a parameter.
def getColourValue(r, g, b):
    r, g, b = r/255.0, g/255.0, b/255.0
    v = max(r, g, b)
    return v

# Finds the background colour comparing the overall value of the colours in the palette.
def getBackgroundColour():
    black = 0
    light = 0
    global palette
    for frequency, colour in palette:
        value = getColourValue(colour[0], colour[1], colour[2])
        if (value > 0.5):
            light += frequency
        else:
            black += frequency
    global whiteBackground
    whiteBackground = (light > black) 

# Gets all colours from the input image and saves them in a global variable.
def getColours(img):
    global palette
    palette = img.getcolors(img.width * img.height)
    getBackgroundColour()
    palette = [colour[1] for colour in palette]     # Delete frequency information.

# Draws the borders and saves the image.
def save(finalImage, genNumber, score):
    if whiteBackground:
        canvas = ImageDraw.Draw(finalImage)
        canvas.line([0,0,0,511], (0,0,0)) # top border
        canvas.line([0,0,511,0], (0,0,0)) # left border
        canvas.line([0,511,511,511], (0,0,0)) # right border
        canvas.line([511,0, 511 ,511], (0,0,0)) # bottom border
    finalImage.save("./final/Size11/X_BC/X_" + str(genNumber) + "gen_" + str(score) + "score.png")

# Genetic algorithm that finds the colours in the input image and draws a replica by pointillism.
def paint(inputImage):
    getColours(inputImage)

    global populationSize
    population = Population(size=populationSize, inputImage=inputImage)
    
    global numGenerationsTotal
    genNumber = 0
    while genNumber <= numGenerationsTotal: 
        print("generation number:" + str(genNumber))
        population.generateNextGeneration()
        if genNumber % 25 == 0:
            save(population.getFirst().print(), genNumber, population.getFirstScore())
        population.printBest()
        genNumber += 1
    
# Tries to open the image and checks whether the size is correct.
def main(inputImage):
    try: 
        inputImage = Image.open(inputImage)
        if inputImage.width != 512 or inputImage.height != 512:
            raise ValueError('Select an image of size 512x512')
        paint(inputImage)
    except IOError:
        logger.error('Image cannot be opened')
        exit()
    except ValueError as error:
        logger.error(str(error))
        exit()

# To execute the program the only parameter needed is the path of the input image.
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', default=None, required=True, help='Image path')
    args = parser.parse_args()
    main(inputImage=args.path)