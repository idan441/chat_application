import uvicorn


# TODO - add better options for production, currently for dev only
if __name__ == "__main__":
    uvicorn.run(app="main:app", host="127.0.0.1", port=8002, reload=True, log_level="debug")
