import pg from 'pg';
if (!process.env.DATABASE_URL) throw new Error('DATABASE_URL required: set up local PostgreSQL before starting API');
const { Pool } = pg;
export const pool = new Pool({connectionString:process.env.DATABASE_URL,max:10,idleTimeoutMillis:30000,connectionTimeoutMillis:5000});
export type Queryable=Pick<pg.PoolClient,'query'>;
export async function transaction<T>(fn:(client:pg.PoolClient)=>Promise<T>):Promise<T> {
 const client=await pool.connect();
 try {await client.query('BEGIN');const value=await fn(client);await client.query('COMMIT');return value;}
 catch(e){await client.query('ROLLBACK');throw e;}
 finally{client.release();}
}
