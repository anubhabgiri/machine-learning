import torch
import torchvision.models as models
import torchvision.transforms as transforms
from transformers import AutoModelForCausalLM, AutoTokenizer
from PIL import Image

  # Visual backbone (MobileNetV3)
visual_backbone = models.mobilenet_v3_small(pretrained=True).features
visual_backbone.eval()

  # MLP projector
projector = torch.nn.Linear(576, 2048)  # Adjust dimensions


  # LLM (TinyLlama)
tokenizer = AutoTokenizer.from_pretrained("TinyLlama/TinyLlama-1.1B-Chat-v1.0")
llm = AutoModelForCausalLM.from_pretrained("TinyLlama/TinyLlama-1.1B-Chat-v1.0")
llm.eval()

  # Example image and text
# image = torch.randn(1, 3, 224, 224)
image_path = "linkedin_feed_sample.png"  # Replace with your image path
image = Image.open(image_path).convert("RGB")  # Ensure RGB format

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),  # ImageNet normalization
])

image_tensor = transform(image).unsqueeze(0) 
text = "Describe this image:"

  # Feature extraction
with torch.no_grad():
    visual_features = visual_backbone(image_tensor).mean(dim=[2, 3])  # Global average pooling

  # Projection
projected_features = projector(visual_features)

  # LLM input
inputs = tokenizer(text, return_tensors="pt")

  # Get the token embeddings
token_embeddings = llm.get_input_embeddings()(inputs.input_ids)

  # Concatenate visual features with token embeddings
combined_embeddings = torch.cat((projected_features.unsqueeze(1), token_embeddings), dim=1)

  # LLM generation
with torch.no_grad():
    outputs = llm.generate(inputs_embeds=combined_embeddings, max_length=300)

print(tokenizer.decode(outputs[0]))