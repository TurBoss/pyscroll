"""
This file contains a classes for accessing data

If you are developing your own map format, please use this
as a template.  Just fill in values that work for your game.
"""
import pytmx

__all__ = ('PyscrollDataAdapter', 'TiledMapData')


class PyscrollDataAdapter(object):
    """ Use this as a template for data adapters
    """
    # the following can be class/instance attributes
    # or properties.  they are listed here as class
    # instances, but use as properties is fine, too.
    tile_size = None         # (int, int): size of each tile in pixels
    map_size = None          # (int, int): size of map in tiles
    visible_layers = None    # list of visible layer integers

    def get_animations(self):
        """ Get tile animation data

        This method is subject to change in the future.

        Must yield tuples that in the following format:
          ( GID, Frames )

          Where Frames is:
          [ (GID, Duration), ... ]

        :returns: sequence
        """
        raise NotImplementedError

    def get_tile_image(self, position):
        """ Return an image for the given position.

        Return None if no tile for position.

        :param position: (x, y, layer) sequence
        :returns: pygame Surface or None
        """
        raise NotImplementedError

    def get_tile_images_by_rect(self, x1, x2, y1, y2, layers):
        """ Given a 2d area, return generator of tile images inside

        Given the coordinates, yield the following tuple for each tile:
          X, Y, Layer Number, pygame Surface, GID

        This method also defines render order by re arranging the
        positions of each tile as it is yielded to the renderer.

        This is an optimization that you can make for your data.
        If you can provide access to tile information in a batch,
        then pyscroll can access data faster and render quicker.

        To implement an optimization, override this method.

        Not like python 'Range': should include the end index!

        GID's are required for animated tiles only.  This value, if not
        used by your game engine, can be 0 or None.

        < The GID requirement will change in the future >

        :param x1: Start x (column) index
        :param x2: Stop x (column) index
        :param y1: Start of y (row) index
        :param y2: Stop of y (row) index
        :param layers: sequence of layer numbers to draw
        :return:
        """
        for layer in layers:
            for y in range(y2, y1 - 1, -1):
                for x in range(x1, x2 + 1):
                    tile = self.get_tile_image((x, y, layer))
                    if tile:
                        yield x, y, layer, tile, 0


class TiledMapData(PyscrollDataAdapter):
    """ For data loaded from pytmx

    Use of this class requires a recent version of pytmx.
    """
    def __init__(self, tmx):
        self.tmx = tmx

    @property
    def tile_size(self):
        """ This is the pixel size of tiles to be rendered
        :return: (int, int)
        """
        return self.tmx.tilewidth, self.tmx.tileheight

    @property
    def map_size(self):
        """ This is the size of the map in tiles
        :return: (int, int)
        """
        return self.tmx.width, self.tmx.height

    @property
    def visible_tile_layers(self):
        """ This must return layer numbers, not objects
        :return:
        """
        return (int(i) for i in self.tmx.visible_tile_layers)

    @property
    def visible_object_layers(self):
        """ This must return layer objects

        This is not required for custom data formats.

        :return:
        """
        return (layer for layer in self.tmx.visible_layers
                if isinstance(layer, pytmx.TiledObjectGroup))

    def get_animations(self):
        for gid, d in self.tmx.tile_properties.items():
            frames = d['frames']
            if not frames:
                continue

            yield gid, frames

    def get_tile_image(self, position):
        try:
            return self.tmx.get_tile_image(*position)
        except ValueError:
            return None

    def get_tile_image_by_gid(self, gid):
        """ Return surface for a gid (experimental)
        """
        return self.tmx.get_tile_image_by_gid(gid)

    def get_tile_images_by_rect(self, x1, x2, y1, y2, layers):
        """ Speed up data access

        More efficient because data is accessed and cached locally
        """
        def do_rev(seq, start, stop):
            return enumerate(seq[start:stop + 1], start)

        images = self.tmx.images
        for layer_no in layers:
            data = self.tmx.layers[layer_no].data
            for y, row in do_rev(data, y1, y2):
                for x, gid in do_rev(row, x1, x2):
                    if gid:
                        yield x, y, layer_no, images[gid], gid
