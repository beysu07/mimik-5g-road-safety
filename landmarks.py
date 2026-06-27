import cv2
import mediapipe as mp


class FaceLandmarkDetector:
    def __init__(
        self,
        static_image_mode=False,
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    ):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=static_image_mode,
            max_num_faces=max_num_faces,
            refine_landmarks=refine_landmarks,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )

        # 6 noktalı göz setleri
        self.LEFT_EYE_IDX = [33, 160, 158, 133, 153, 144]
        self.RIGHT_EYE_IDX = [362, 385, 387, 263, 373, 380]

        # ağız dış konturdan temel noktalar
        self.MOUTH_IDX = [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 308]

    def get_landmarks(self, frame):
        if frame is None:
            return None

        h, w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb)

        if not results.multi_face_landmarks:
            return None

        face_landmarks = results.multi_face_landmarks[0]
        landmarks_px = []

        for lm in face_landmarks.landmark:
            x = int(lm.x * w)
            y = int(lm.y * h)
            landmarks_px.append((x, y))

        return landmarks_px

    def get_left_eye_points(self, landmarks):
        if landmarks is None:
            return None
        return [landmarks[i] for i in self.LEFT_EYE_IDX]

    def get_right_eye_points(self, landmarks):
        if landmarks is None:
            return None
        return [landmarks[i] for i in self.RIGHT_EYE_IDX]

    def get_mouth_points(self, landmarks):
        if landmarks is None:
            return None
        return [landmarks[i] for i in self.MOUTH_IDX]

    def close(self):
        self.face_mesh.close()