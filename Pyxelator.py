from PIL import Image, ImageDraw
from operator import itemgetter
from random import randint, random
import numpy
import argparse
import logging
logger = logging.getLogger()

colors = []                 # colors of the input image
whiteBackground = True      # background of the image
numGenerationsTotal = 200   # number of total generations


class Dot:
    def __init__(self, x, y, color):
        self.color = color  # (red, green, blue)
        self.x = x          
        self.y = y       

    def mutate(self):
        global colors
        self.color = colors[randint(0,len(colors)-1)][1]  

# individual of the population, a drawn image that tries to replicate the input image
class Replica:  
    def __init__(self):
        self.dots = []
        # a replica contains 10,404 dots (102 * 102, because of 512 / 5 = 102)

    def getDots(self):
        return self.dots

    # generates an Image with the dots painted in it    
    def print(self):
        global whiteBackground
        if whiteBackground: 
            resultImage = Image.new("RGB", (512,512), (255, 255, 255))
        else:
            resultImage = Image.new("RGB", (512,512), (0, 0, 0))

        canvas = ImageDraw.Draw(resultImage)
        for dot in self.dots:
            canvas.ellipse([dot.x, dot.y, dot.x+4,dot.y+4], fill=dot.color)
        
        return resultImage
        
    # generates the dots with a random color of the palette
    def generateRandom(self):
        global colors
        i = 1
        while i < 510:
            j = 1
            while j < 510:
                self.dots.append(Dot(x=i, y=j, color=colors[randint(0,len(colors)-1)][1]))
                j += 5
            i += 5   
        return self

    # scores itself by converting itself and the input image to arrays
    # the score indicates how different they are (0% very similar, 100% completely different)
    # from https://www.raspberrypi.org/forums/viewtopic.php?t=195181
    def getFitnessScore(self, inputImage):
        selfPrinted = self.print()
        arraySelf = numpy.array(selfPrinted).astype(numpy.int)
        arrayInput = numpy.array(inputImage).astype(numpy.int)
        return (numpy.abs(arraySelf-arrayInput).sum() / 255.0 * 100) / arrayInput.size

    # the dots of the replica are filled with each individual with a probability of 50%
    def crossover(self, firstIndividual, secondIndividual):
        firstDots = firstIndividual[0].getDots()
        secondDots = secondIndividual[0].getDots()
        for i in range(0, len(firstDots)):
            if random() < 0.5:
                self.dots.append(firstDots[i])
            else:
                self.dots.append(secondDots[i])

    def mutate(self):
        for dot in self.dots:
            if randint(0,8192) == 1:
                dot.mutate()
                
# all replicas of the input image
class Population:
    def __init__(self, size, inputImage):
        self.size = size
        self.population = []
        self.inputImage = inputImage
        self.generateFirstPopulation()

    # generates first population completely random
    def generateFirstPopulation(self):
        for i in range(0, self.size-1):
            replica = Replica().generateRandom()
            self.population.append((replica,replica.getFitnessScore(self.inputImage)))
            self.sort()

    # generates next generation
    def generateNextGeneration(self):
        #individuals = [individual[0] for individual in population]
        
        half = (len(self.population) + 1) / 2
        newPopulation = self.population[:int(half)]

        for i in range(0, int(half)):
            newIndividual = Replica()
            newIndividual.crossover(newPopulation[i], newPopulation[randint(0, int(half)-1)])
            #newIndividual.mutate()
            newPopulation.append((newIndividual,newIndividual.getFitnessScore(self.inputImage)))

        self.population = newPopulation
        self.sort()

    # returns the first replica, as it is sorted, it is always the best one 
    def getFirst(self):
        return self.population[0][0]

    # prints the population's score fitness
    def print(self):
        for individual in self.population:
            print(individual[1])

    # sorts the population by its fitness score
    def sort(self):
        self.population.sort(key=lambda tup: tup[1])

# finds the HSV's value of the color sent as a parameter.
def getColorValue(r, g, b):
    r, g, b = r/255.0, g/255.0, b/255.0
    v = max(r, g, b)
    return v

# gets all colors from the image and saves them in a global variable sorted by frequency.
def getColors(img):
    global colors
    colors = img.getcolors(img.width * img.height)
    # colors.sort(key=lambda tup: tup[0], reverse=True) # TODO -> is this necessary?

# finds the background color comparing the overall value of colors.
def getBackgroundColor():
    """ TODO -> maybe it would be better to paint it in the most common color 
            it will make it more efficient but the output may not be as pretty
        and even maybe it should be better to group the colors by more general colors
        and paint the background of that general color."""
    black = 0
    light = 0
    for _, color in colors:
        value = getColorValue(color[0], color[1], color[2])
        if (value > 0.5):
            light += 1
        else:
            black += 1
    global whiteBackground
    whiteBackground = (light > black)   

# draws the borders and saves the image
def save(finalImage, genNumber):
    canvas = ImageDraw.Draw(finalImage)
    canvas.line([0,0,0,511], (0,0,0)) # top border
    canvas.line([0,0,511,0], (0,0,0)) # left border
    canvas.line([0,511,511,511], (0,0,0)) # right border
    canvas.line([511,0, 511 ,511], (0,0,0)) # bottom border
    finalImage.save("testNoMutationF" + str(genNumber) + ".jpg")

# genetic algorithm that finds the colors in the input image and draws a replica by pointillism
def paint(inputImage):
    getColors(inputImage)
    getBackgroundColor()
    
    population = Population(size=50, inputImage=inputImage)
    
    genNumber = 0
    global numGenerationsTotal
    while genNumber <= numGenerationsTotal: 
        print("generation number:" + str(genNumber))
        population.generateNextGeneration()
        if genNumber % 25 == 0:
            save(population.getFirst().print(),genNumber)
        population.print()
        genNumber += 1
    

    

# tries to open the image and checks whtehr the size is correct or not
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


# to execute the program the only parameter needed is the path of the input image
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', default=None, required=True, help='Image path')
    args = parser.parse_args()
    main(inputImage=args.path)