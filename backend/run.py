"""Optional company PaaS starting file. Production guards are inside app.main."""
import os
import uvicorn
if __name__ == '__main__':
    port=int(os.environ.get('PORT','8000'))
    if not 1<=port<=65535:raise ValueError('PORT is invalid.')
    uvicorn.run('app.main:app',host='0.0.0.0',port=port,workers=1)
