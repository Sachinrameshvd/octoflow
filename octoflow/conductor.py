from onnxruntime import InferenceSession, SessionOptions, ExecutionMode

class OptimizedModel:
    def __init__(self, model_path):
        self.session = InferenceSession(model_path, SessionOptions(), providers=['CUDAExecutionProvider'])
        self.session.set_execution_mode(ExecutionMode.ORT_ENABLE_ONNXRUNTIME_LOGGING)

    def infer(self, input_data):
        return self.session.run(None, {'input_name': input_data})