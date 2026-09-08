import {spawnSync} from 'node:child_process'
const r=spawnSync(process.env.BASE_PYTHON??'python',['../scripts/check_architecture.py'],{stdio:'inherit'});process.exit(r.status??1)
