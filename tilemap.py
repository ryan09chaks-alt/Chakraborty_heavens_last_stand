# Loads tile-based maps from .txt files

class Map:
    def __init__(self, filename):
        self.data = []
        with open(filename, 'rt') as f:
            for line in f:
                self.data.append(line.strip())  # Store each line

        self.tilewidth = len(self.data[0])   # Map columns
        self.tileheight = len(self.data)     # Map rows
        self.width = self.tilewidth * 32     # Pixel width
        self.height = self.tileheight * 32   # Pixel height
