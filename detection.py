class BlinkCounter:
    def __init__(
        self,
        close_threshold=0.22,
        open_threshold=0.24,
        min_closed_frames=2,
        cooldown_frames=6,
    ):
        self.close_threshold = close_threshold
        self.open_threshold = open_threshold
        self.min_closed_frames = min_closed_frames
        self.cooldown_frames = cooldown_frames

        self.blink_count = 0
        self.eye_closed = False
        self.closed_frames = 0
        self.cooldown_counter = 0

    def update(self, ear_value):
        """
        ear_value: EMA EAR gibi stabilize edilmiş değer
        returns:
            blink_detected, eye_closed
        """
        blink_detected = False

        if ear_value is None:
            return blink_detected, self.eye_closed

        # Cooldown aktifse azalt
        if self.cooldown_counter > 0:
            self.cooldown_counter -= 1

        # Göz şu anda açık kabul ediliyorsa,
        # kapanması için close_threshold altına düşmeli
        if not self.eye_closed:
            if ear_value < self.close_threshold:
                self.eye_closed = True
                self.closed_frames = 1
            else:
                self.closed_frames = 0

        # Göz şu anda kapalı kabul ediliyorsa,
        # açılması için open_threshold üstüne çıkmalı
        else:
            if ear_value < self.open_threshold:
                self.closed_frames += 1
            else:
                # Kapalı -> açık geçişi
                if (
                    self.closed_frames >= self.min_closed_frames
                    and self.cooldown_counter == 0
                ):
                    self.blink_count += 1
                    blink_detected = True
                    self.cooldown_counter = self.cooldown_frames

                self.eye_closed = False
                self.closed_frames = 0

        return blink_detected, self.eye_closed

    def reset(self):
        self.blink_count = 0
        self.eye_closed = False
        self.closed_frames = 0
        self.cooldown_counter = 0