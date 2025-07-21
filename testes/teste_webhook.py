from fastapi import FastAPI, Request

app = FastAPI()

# Pegue esse segredo na hora de criar o webhook no WooCommerce
WC_WEBHOOK_SECRET = "J~}Q%f^B#.@:J<mt]7a^=c4d_NVU]o0.0c(RI{8=,bPptHm[!@"

@app.post("/webhook")
async def webhook_receiver(request: Request): 
    raw_body = await request.body()
    print(f'!!!!!!!!! {raw_body}')

    return {"ok": True}
