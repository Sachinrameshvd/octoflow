
import onnx
from onnxruntime import InferenceSession, SessionOptions

def optimize_onnx_model(model_path: str, output_path: str) -> None:
    session_options = SessionOptions()
    session_options.graph_optimization_level = SessionOptions.GraphOptimizationLevel.ORT_ENABLE_ALL
    session = InferenceSession(model_path, session_options=session_options)
    optimized_model = session.get_model()
    onnx.save(optimized_model, output_path)

if __name__ == "__main__":
    input_model_path = "path/to/your/model.onnx"
    output_model_path = "path/to/your/optimized_model.onnx"
    optimize_onnx_model(input_model_path, output_model_path)
