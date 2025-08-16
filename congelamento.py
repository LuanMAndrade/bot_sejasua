import asyncio

pausas = {}

def congelamento(data, sender):
    if data["data"]["key"]["fromMe"] == True and data['data']['source'] == 'ios':  
            pausas[sender] = asyncio.get_event_loop().time() + 3600
            print(f"PAUSA ativada para {sender} por {3600} segundos")
            return {"status": f"chatbot pausado para {sender}"}
        
    agora = asyncio.get_event_loop().time()
    if sender in pausas:
        if agora < pausas[sender]:
            print(f"{sender} ainda em pausa. Ignorando chatbot.")
            return {"status": f"em pausa até {pausas[sender] - agora:.1f}s"}
        else:
            del pausas[sender]  # tempo expirou