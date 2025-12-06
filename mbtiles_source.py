import sqlite3
from kivy_garden.mapview.source import MapSource

class MBTilesMapSource(MapSource):
    """
    Custom MapSource that loads map tiles from an MBTiles SQLite database.
    Supports PNG/JPG tiles stored in the 'tiles' table.
    """

    def __init__(self, mbtiles_path):
        super().__init__(
            min_zoom=1,
            max_zoom=19,
            attribution="Offline Map",
            tile_size=256
        )

        self.mbtiles_path = mbtiles_path
        self.conn = sqlite3.connect(self.mbtiles_path)
        self.cursor = self.conn.cursor()

    def get_tile(self, zoom, x, y, *args):
        # MBTiles stores TMS coordinates (Y is flipped)
        flipped_y = (2**zoom - 1) - y

        row = self.cursor.execute(
            "SELECT tile_data FROM tiles WHERE zoom_level=? AND tile_column=? AND tile_row=?",
            (zoom, x, flipped_y)
        ).fetchone()

        if row:
            return row[0]  # raw PNG/JPG bytes

        return None
