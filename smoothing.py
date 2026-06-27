class EMAFilter:
    def __init__(self, alpha=0.3):
        """
        alpha arttıkça yeni değere daha hızlı tepki verir.
        alpha küçüldükçe daha fazla yumuşatır.
        """
        self.alpha = alpha
        self.value = None

    def update(self, current_value):
        """
        current_value None ise mevcut smooth değeri bozmaz.
        """
        if current_value is None:
            return self.value

        if self.value is None:
            self.value = current_value
        else:
            self.value = (
                self.alpha * current_value
                + (1.0 - self.alpha) * self.value
            )

        return self.value

    def reset(self):
        self.value = None