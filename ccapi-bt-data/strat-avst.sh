#!/usr/bin/bash
set -v

echo "Start strat-avst"
# Download exchange data : exchange, pair, dates
cd /home/ajjc/hca/crypto_data
python3 download_historical_market_data.py --exchange kucoin --base-asset btc --quote-asset usdt --start-date 2022-02-01 --end-date 2022-02-11 --historical-market-data-directory kucoin-2022-02-11

# Run exchange data: All configs and paths in file config_50_50.env
# WARNING: EXCHANGE keys must be filled in by hand if needed in <config>.env file
cd /home/ajjc/hca/ccapi/app/build/src/spot_market_making 
 export $(grep -v '^#' config_50_50.env | xargs)
./spot_market_making
 echo "End strat-avst"
