from datetime import datetime
class Frame:
    def __init__(self, image, cam_id):
        self.image = image
        self.cam_id = cam_id
        self.timestamp = datetime.now().astimezone().isoformat(" ", "seconds")
        self.boxes = []
