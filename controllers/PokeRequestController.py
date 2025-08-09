import json 
import logging

from fastapi import HTTPException
from models.PokeRequest import PokeRequest
from utils.database import execute_query_json
from utils.AQueue import AQueue
from utils.ABlob import ABlob


# configurar el logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def select_pokemon_request(id: int):
    try:
        query = "select * from pokequeue.request where id = ?"
        params = (id,)
        result = await execute_query_json(query, params)
        result_dict = json.loads(result)
        return result_dict
    except Exception as e:
        logger.error(f"Error selecting report request {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


async def update_pokemon_request(pokemon_request: PokeRequest) -> dict:
    try:
        query = "exec pokequeue.update_poke_request ?, ?, ?"
        if not pokemon_request.url:
            pokemon_request.url = ""

        params = (pokemon_request.id, pokemon_request.status, pokemon_request.url)
        result = await execute_query_json(query, params, True)
        result_dict = json.loads(result)
        return result_dict
    except Exception as e:
        logger.error(f"Error updating report request {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


async def insert_pokemon_request(pokemon_request: PokeRequest) -> dict:
    try:
        # Actualizar el stored procedure para incluir sample_size
        query = "exec pokequeue.create_poke_request ?, ?"
        params = (pokemon_request.pokemon_type, pokemon_request.sample_size)
        result = await execute_query_json(query, params, True)
        result_dict = json.loads(result)

        # Enviar solo el resultado básico a la cola (sin modificar)
        # La Azure Function obtendrá el sample_size directamente de la BD
        await AQueue().insert_message_on_queue(json.dumps(result_dict))

        return result_dict
    except Exception as e:
        logger.error(f"Error inserting report request {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


async def get_all_request() -> dict:
    try:
        query = """
            SELECT 
                r.id as ReportId, 
                s.description as Status,
                r.type as PokemonType,
                r.sample_size as SampleSize,
                r.url,
                r.created_at,
                r.updated_at
            FROM pokequeue.request r 
            INNER JOIN pokequeue.status s 
            ON r.id_status = s.id 
        """
        result = await execute_query_json(query)
        result_dict = json.loads(result)
        blob = ABlob()
        for record in result_dict:
            id = record['ReportId']
            # Solo agregar SAS si hay URL
            if record['url'] and record['url'].strip():
                record['url'] = f"{record['url']}?{blob.generate_sas(id)}"
            else:
                record['url'] = None
        return result_dict
    except Exception as e:
        logger.error(f"Error getting report requests {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


async def delete_pokemon_request(id: int) -> dict:
    try:
        # Verificar si el reporte existe
        query_check = "SELECT id FROM pokequeue.request WHERE id = ?"
        params_check = (id,)
        result_check = await execute_query_json(query_check, params_check)
        existing_report = json.loads(result_check)
        
        if not existing_report:
            raise HTTPException(status_code=404, detail="Report not found")

        blob = ABlob()
        blob_name = f"poke_report_{id}.csv"
        try:
            await blob.delete_blob(blob_name)
            logger.info(f"Deleted blob {blob_name}")
        except Exception as e:
            logger.warning(f"Could not delete blob {blob_name}: {e}")

        query_delete = "DELETE FROM pokequeue.request WHERE id = ?"
        params_delete = (id,)
        result_delete = await execute_query_json(query_delete, params_delete, True)
        
        return {"status": "success", "message": f"Report {id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting report request {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")