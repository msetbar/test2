from config.snowflake_config import config
from loguru import logger as log
import snowflake.connector
from snowflake.connector import SnowflakeConnection


_CCKM_QUERY = """
SELECT DISTINCT
k.KNLG_ARTC_VRSN_ID AS "Id",
k.ARTC_NBR AS "ArticleNumber", k.TITL AS "Title", k.URL_NM AS "UrlName", k.ARTC_STS_FORML AS "PublishStatus",
k.BW_ARTC_DTL AS "BW_Article_Details__c",   --Article content
k.BW_ARTC_SUMR AS "BW_Article_Summary__c",  
k.BW_TXNMY_GRP_1, k.BW_TXNMY_GRP_2, k.BW_TXNMY_GRP_3  -- taxonomy group

FROM
AZACCP.SDW_ACC_VIEWS.SLSFRC_SYNC_BW_DATA_CAT dc,
AZACCP.SDW_ACC_VIEWS.SLSFRC_SYNC_KNLG_DATA_CAT_SEL cs,
AZACCP.SDW_ACC_VIEWS.SLSFRC_SYNC_KNLG_KAV k,
AZACCP.SDW_ACC_VIEWS.SLSFRC_SYNC_KNLG_ARHV ka
WHERE
/* business and online, published articles only */
((dc.DATACAT_NM LIKE 'BCSS%') OR (dc.DATACAT_NM LIKE 'BRM%'))  -- includes all BCSS related articles: 3775 2023/10/19
AND cs.DATA_CAT_NM = dc.DATACAT_NM
AND k.ARTC_NBR = ka.KM_ARTC_KA_ID
AND cs.PRNT_ID = ka.ARTC_VRSN_ID
AND PBLS_STS = 'Online'
AND k.ARTC_STS_FORML = 'Published'
AND ka.KM_VRSN_NBR = k.VRSN_NBR
AND (k.BW_ARTC_DTL IS NOT NULL OR k.BW_ARTC_DTL != '')  -- too small content exclude
"""


class SnowflakeClient(object):
    ctx: SnowflakeConnection

    def __init__(self):
        # assuming that we're using the connection.toml file to connect
        # else we can use environment variables
        self.ctx = snowflake.connector.connect(
            user=config.username,
            password=config.password,
            account=config.account,
            warehouse=config.warehouse,
            database=config.database,
            role=config.role,
        )

    def __del__(self):
        # automatically closing the connection once finished with object
        self.close_connection()

    def get_cckm_data(self) -> list[dict]:
        with self.ctx.cursor(snowflake.connector.DictCursor) as cur:
            cur.execute(_CCKM_QUERY)
            results = cur.fetchall()
            log.info(f"Extracted {len(results)} from snowflake...")
            for result in results:
                for key, val in result.items():
                    if val is None:
                        result[key] = str()
            return results

    def close_connection(self):
        log.info("Closing the connection...")
        self.ctx.close()
