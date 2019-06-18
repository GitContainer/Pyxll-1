class MissingAssetsException(Exception):
    def __str__(self):
        return "Missing Assets to start the Model"
