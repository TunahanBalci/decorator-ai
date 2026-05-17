import os
import json
from google import genai
from google.genai import types
from PIL import Image
from pydantic import BaseModel, Field
from typing import List

# 1. Gemini'ın üreteceği JSON çıktısını garanti altına almak için Pydantic Şeması tanımlıyoruz
class FurnitureAttributes(BaseModel):
    category: str = Field(description="E.g., 'Sehpa', 'Koltuk', 'Yatak', 'Masa'")
    room_type: List[str] = Field(description="E.g., ['living_room'], ['bedroom'], ['dining_room']")
    main_color: str = Field(description="The dominant color of the furniture")
    secondary_colors: List[str] = Field(description="Any side colors visible")
    material: List[str] = Field(description="E.g., ['wood'], ['metal'], ['fabric'], ['leather']")
    style: List[str] = Field(description="E.g., ['modern'], ['japandi'], ['minimalist'], ['bohemian'], ['scandinavian']")
    temperature: str = Field(description="Must be one of: 'warm', 'cold', 'neutral'")
    dimensions: str = Field(description="Extract dimensions if mentioned in text (e.g., '70x100 cm'), otherwise 'unknown'")
    availability: str = Field(description="Default to 'in_stock' unless metadata says otherwise")
    visual_tags: List[str] = Field(description="3 to 5 descriptive visual tags, e.g., ['soft edges', 'thin legs', 'bulky']")

class DesignLabeler:
    def __init__(self, api_key: str):
        # Gemini 3 Flash / 2.5 yapısına uygun client başlatma
        self.client = genai.Client(api_key=api_key)

    def analyze_furniture(self, image_path: str, raw_data: dict) -> FurnitureAttributes:
        prompt = f"""
        You are an expert interior designer and computer vision agent.
        Analyze the provided furniture image and its scraped metadata to enrich our database.
        
        Product Name: {raw_data.get('name', '')}
        Product Description: {raw_data.get('description', '')}
        
        Fill every field in the required JSON schema accurately. 
        If a field cannot be inferred from the image or text, use 'unknown'.
        """
        
        contents = [prompt]
        
        # Eğer yerel bir görsel yolu varsa listeye ekle
        if image_path and os.path.exists(image_path):
            try:
                image = Image.open(image_path)
                contents.append(image)
            except Exception as e:
                print(f"Görsel açılamadı ({image_path}): {e}")

        # Structured Outputs (Yapılandırılmış Çıktı) özelliğini aktif ediyoruz.
        # Bu sayede Gemini asla ekstra açıklama yazmaz, SADECE şemaya uygun saf JSON döner.
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=FurnitureAttributes,
            temperature=0.2 # Daha kararlı ve deterministik tahminler için düşürdük
        )
        
        response = self.client.models.generate_content(
            model='gemini-2.5-flash', # Veya projedeki güncel flash modeli
            contents=contents,
            config=config
        )
        
        # Gelen string çıktıyı Pydantic modeline dönüştürüp valide ediyoruz
        return FurnitureAttributes.model_validate_json(response.text)