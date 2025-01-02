import json
from fastapi import logger
import requests
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)

PIPEFY_API_URL = "https://api.pipefy.com/graphql"

def pipefy_request(query: str, variables: Dict, api_token: str) -> Dict:
    headers = {"Authorization": f"Bearer {api_token}"}
    logger.info(f"Sending request to Pipefy API. Query: {query}, Variables: {variables}")
    response = requests.post(PIPEFY_API_URL, json={"query": query, "variables": variables}, headers=headers)
    
    logger.info(f"Pipefy API response status code: {response.status_code}")
    logger.info(f"Pipefy API response content: {response.text}")
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Pipefy API error: {response.status_code} - {response.text}")
    
def get_pipe_phases(pipe_id: str, api_token: str) -> List[Dict]:
    query = """
    query GetPipePhases($pipeId: ID!) {
      pipe(id: $pipeId) {
        phases {
          id
          name
        }
      }
    }
    """
    variables = {"pipeId": pipe_id}
    
    try:
        data = pipefy_request(query, variables, api_token)
        return data["data"]["pipe"]["phases"]
    except Exception as e:
        raise Exception(f"Error fetching pipe phases: {str(e)}")

def get_phase_fields(phase_id: str, api_token: str) -> List[Dict]:
    query = """
    query GetPhaseFields($phaseId: ID!) {
      phase(id: $phaseId) {
        fields {
          id
          label
          type
        }
      }
    }
    """
    variables = {"phaseId": phase_id}
    
    try:
        data = pipefy_request(query, variables, api_token)
        return data["data"]["phase"]["fields"]
    except Exception as e:
        raise Exception(f"Error fetching phase fields: {str(e)}")

def update_card_fields(card_id: str, field_updates: Dict, api_token: str) -> Tuple[bool, str]:
    mutation = """
    mutation UpdateCardField($input: UpdateCardFieldInput!) {
      updateCardField(input: $input) {
        success
      }
    }
    """
    
    try:
        for field_id, new_value in field_updates.items():
            # Garantir que o valor seja uma string não vazia
            if new_value is None or new_value == '':
                continue  # Pular campos vazios
            
            string_value = str(new_value).strip()
            if not string_value:
                continue  # Pular se ainda estiver vazio após strip()

            variables = {
                "input": {
                    "card_id": str(card_id),
                    "field_id": str(field_id),
                    "new_value": string_value
                }
            }
            
            logger.info(f"Sending update for card {card_id}, field {field_id}: {string_value}")
            response = pipefy_request(mutation, variables, api_token)
            logger.info(f"Pipefy API response: {response}")
            
            if 'errors' in response:
                error_message = "; ".join([error['message'] for error in response['errors']])
                return False, f"Pipefy API error: {error_message}"
            
            if 'data' not in response or 'updateCardField' not in response['data']:
                return False, f"Unexpected response structure from Pipefy API: {response}"
            
            if not response['data']['updateCardField']['success']:
                return False, f"Failed to update field {field_id} for card {card_id}"
        
        return True, "All fields updated successfully"
    except Exception as e:
        logger.error(f"Error updating card fields: {str(e)}", exc_info=True)
        return False, f"Error updating card fields: {str(e)}"

def get_pipe_fields(pipe_id: str, api_token: str) -> List[Dict]:
    # Extrair apenas o número do pipe se for uma URL
    if pipe_id.startswith('http'):
        pipe_id = pipe_id.split('/')[-1]

    query = """
    query ($pipeId: ID!) {
      pipe(id: $pipeId) {
        start_form_fields {
          id
          label
          type
        }
        phases {
          fields {
            id
            label
            type
          }
        }
      }
    }
    """
    variables = {"pipeId": pipe_id}
    
    try:
        data = pipefy_request(query, variables, api_token)
        
        # Log detalhado da resposta
        logger.info(f"Resposta da API de campos: {json.dumps(data, indent=2)}")
        
        # Verificar se há erros na resposta
        if 'errors' in data:
            error_messages = [error.get('message', 'Unknown error') for error in data['errors']]
            raise Exception(f"Pipefy API errors: {'; '.join(error_messages)}")
        
        # Verificar se o pipe existe
        if not data.get('data', {}).get('pipe'):
            raise Exception("Pipe não encontrado ou acesso negado")
        
        # Coletar campos do formulário inicial e das fases
        start_form_fields = data['data']['pipe'].get('start_form_fields', [])
        phase_fields = [
            field 
            for phase in data['data']['pipe'].get('phases', []) 
            for field in phase.get('fields', [])
        ]
        
        # Combinar campos
        all_fields = start_form_fields + phase_fields
        
        return all_fields
    
    except Exception as e:
        logger.error(f"Erro ao buscar campos do pipe: {str(e)}", exc_info=True)
        raise Exception(f"Error fetching pipe fields: {str(e)}")

def get_field_id_by_label(pipe_id: str, field_label: str, api_token: str) -> str:
    fields = get_pipe_fields(pipe_id, api_token)
    for field in fields:
        if field['label'].lower() == field_label.lower():
            return field['id']
    raise Exception(f"Field with label '{field_label}' not found in pipe {pipe_id}")

def get_field_labels_and_ids(pipe_id: str, api_token: str) -> Dict[str, str]:
    fields = get_pipe_fields(pipe_id, api_token)
    return {field['label']: field['id'] for field in fields}

def get_pipe_members(pipe_id: str, api_token: str) -> List[Dict]:
    query = """
    query ($pipeId: ID!) {
      pipe(id: $pipeId) {
        members {
          user {
            id
            name
            email
          }
        }
      }
    }
    """
    variables = {"pipeId": pipe_id}
    
    try:
        data = pipefy_request(query, variables, api_token)
        if not data or 'data' not in data or 'pipe' not in data['data']:
            raise Exception(f"Invalid response from Pipefy API: {data}")
        
        return data['data']['pipe']['members']
    except Exception as e:
        logger.error(f"Error fetching pipe members: {str(e)}")
        raise Exception(f"Error fetching pipe members: {str(e)}")

def move_cards(card_ids: List[str], destination_phase_id: str, api_token: str) -> Tuple[bool, str]:
    mutation = """
    mutation MoveCardToPhase($input: MoveCardToPhaseInput!) {
      moveCardToPhase(input: $input) {
        card {
          id
          title
        }
      }
    }
    """
    
    results = []
    
    try:
        for card_id in card_ids:
            variables = {
                "input": {
                    "card_id": str(card_id),
                    "destination_phase_id": str(destination_phase_id)
                }
            }
            
            logger.info(f"Moving card {card_id} to phase {destination_phase_id}")
            response = pipefy_request(mutation, variables, api_token)
            logger.info(f"Pipefy API response: {response}")
            
            # Verificar a estrutura da resposta
            if 'errors' in response:
                error_message = "; ".join([error['message'] for error in response['errors']])
                results.append({
                    'card_id': card_id,
                    'success': False,
                    'message': f"Pipefy API error: {error_message}"
                })
                continue
            
            if 'data' not in response or 'moveCardToPhase' not in response['data']:
                results.append({
                    'card_id': card_id,
                    'success': False,
                    'message': f"Unexpected response structure from Pipefy API: {response}"
                })
                continue
            
            # Se chegou aqui, o card foi movido com sucesso
            results.append({
                'card_id': card_id,
                'success': True,
                'message': f"Card {card_id} moved successfully"
            })
        
        # Verificar se todos os cards falharam
        if all(not result['success'] for result in results):
            return False, "No cards could be moved"
        
        return True, results
    
    except Exception as e:
        logger.error(f"Error moving cards: {str(e)}", exc_info=True)
        return False, f"Error moving cards: {str(e)}"
