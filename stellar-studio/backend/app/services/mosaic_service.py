# app/services/mosaic_service.py
from astropy.io import fits
from PIL import Image
import numpy as np

class MosaicService:
    def create_mosaic_from_fits(self, fits_files: list, minio_client) -> str:
        images = []
        for fits_file in fits_files:
            # Récupérer le fichier FITS depuis MinIO
            data = minio_client.get_object("fits-files", fits_file).read()
            
            # Convertir FITS en image
            with fits.open(BytesIO(data)) as hdul:
                img_data = hdul[0].data
                # Normalisation pour conversion en PNG
                img_data = self.normalize_fits_data(img_data)
                images.append(Image.fromarray(img_data))

        # Créer la mosaïque
        mosaic_width = 800
        mosaic_height = 800 // len(images) * len(images)
        mosaic = Image.new("L", (mosaic_width, mosaic_height))

        # Assembler la mosaïque
        for idx, img in enumerate(images):
            img = img.resize((mosaic_width, mosaic_height // len(images)))
            mosaic.paste(img, (0, idx * (mosaic_height // len(images))))

        # Sauvegarder dans MinIO
        mosaic_path = f"mosaics/{uuid.uuid4()}.png"
        with BytesIO() as bio:
            mosaic.save(bio, format='PNG')
            minio_client.put_object(
                "fits-files", 
                mosaic_path, 
                bio.getvalue(),
                len(bio.getvalue()),
                content_type="image/png"
            )
        return mosaic_path
