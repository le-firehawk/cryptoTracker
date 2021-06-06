import os, subprocess, sys, requests, time
from plyer import notification
arguments = sys.argv[1:]


def convertCurrency(price, currency):
    data = requests.get("https://api.exchangerate-api.com/v4/latest/USD").json()
    allCurrencies = data["rates"]
    price = round(price * allCurrencies[currency], 2)
    return price


def getMarketData():
    rawMarketData = subprocess.Popen("coinmon", stdout=subprocess.PIPE, shell=True).communicate()[0]
    marketData = rawMarketData.decode("utf-8").encode("ascii", "ignore").decode().split("\n")
    while "" in marketData:
        del(marketData[marketData.index("")])
    source, tickTime = marketData[0].split("from")[1].split("at")
    del(marketData[1:4])
    return source, tickTime, marketData


def processParameters():
    loopTick, verbose, display, tickInterval = False, False, False, None
    if "--no-display" not in arguments:
        if "-v" in arguments:
            verbose = True
        display = True
    if "--loop" in arguments:
        loopTick = True
        if "-t" in arguments:
            tickInterval = int(arguments[arguments.index("-t")+1])
        else:
            tickInterval = 5
    if "-c" in arguments:
        currency = arguments[arguments.index("-c")+1]
        if currency.strip() != "USD":
            needToConvert = True
        else:
            needToConvert = False
    else:
        currency = "USD"
        needToConvert = False
    return verbose, display, loopTick, tickInterval, currency, needToConvert


def getCoinInfo(marketData, **kwargs):
    coinInfo, oldCoinValue = [], kwargs.get("oldData", None)
    for index in range(1, len(marketData), 2):
        dataRow = marketData[index].split()
        coinIndex, coinType, coinPrice, coinAdjustment, coinMarketCap, coinSupply, coin24Volume = int(dataRow[1]), dataRow[3], float(dataRow[5]), float(dataRow[7].replace("\x1b[31m", "").replace("\x1b[39m", "").replace("\x1b[32m", "").replace("\x1b[39m", "").replace("%", "")), dataRow[9], dataRow[11], dataRow[13]
        if oldCoinValue != None and oldCoinValue[1] in coinType and oldCoinValue[0] != None:
            if oldCoinValue[0] < round(coinPrice, 2):
                positiveMove = True
            else:
                positiveMove = False
        else:
            if "-" in str(coinAdjustment):
                positiveMove = False
            else:
                positiveMove = True
        coinInfo.append([coinIndex, coinType, coinPrice, coinAdjustment, coinMarketCap, coinSupply, coin24Volume, positiveMove])
    return coinInfo


try:
    criticalError = False
    source, tickTime, marketData = getMarketData()
    verbose, display, loopTick, tickInterval, currency, needToConvert = processParameters()
    coinInfo = getCoinInfo(marketData)
except Exception as e:
    criticalError, crashError = True, e


if criticalError:
    print("ERROR:")
    print(crashError)
else:
    if verbose:
        print("Starting up!")


if not loopTick:
    if display:
        print("Coins:")
        print("".join([f"{coin[1]}\n" for coin in coinInfo]))
        selectedCoin = input("Select Coin: ")
    else:
        selectedCoin = "BTC"
    for coinRow in coinInfo:
        if selectedCoin in coinRow[1]:
            coinIndex, coinType, coinPrice, coinAdjustment, coinMarketCap, coinSupply, coin24Volume, positiveMove = coinRow
            break
    if needToConvert:
        coinPrice, rawPrice = convertCurrency(coinPrice, currency), round(coinPrice, 2)
    else:
        coinPrice, rawPrice = round(coinPrice, 2), round(coinPrice, 2)
    if display:
        print(f"Summary of crypto market at {tickTime.strip()}")
        print(f"Sourced from {source.strip()}")
        print(f"Coin {coinIndex} ({coinType}):")
        print(f"Coin Price: ${coinPrice} {currency}")
        if positiveMove:
            print("\033[32m", end="")
        else:
            print("\033[31m", end="")
        print(f"Change (24H): {coinAdjustment}%\033[0m")
        print(f"Market Cap: {coinMarketCap}")
        print(f"Coin Supply: {coinSupply}")
        print(f"Coin Volume (24H): {coin24Volume}")
    else:
        notification.notify(
                title=coinType,
                message=f"{f'Increase of' if positiveMove else f'Decrease of'} {coinAdjustment}% in the past 24 hours!\nCurrently sitting at ${coinPrice} {currency}!",
                app_name='Open Source Crypto Tracker',
                timeout=5
            )
else:
    if "-o" in arguments:
        selectedCoin = arguments[arguments.index("-o")+1].strip()
    else:
        selectedCoin = "BTC"
    for coin in coinInfo:
        if selectedCoin in coin:
            selectedCoinIndex = coinInfo.index(coin)
    firstIteration, lastCoinPrice, lastCoinAdjustment = True, None, 1
    while True:
        try:
            source, tickTime, marketData = getMarketData()
            coinInfo = getCoinInfo(marketData, oldData=[lastCoinPrice, selectedCoin])
            try:
                lastCoinPrice = convertCurrency(lastCoinPrice, currency)
            except:
                pass
            coinIndex, coinType, coinPrice, coinAdjustment, coinMarketCap, coinSupply, coin24Volume, positiveMove = coinInfo[selectedCoinIndex]
            if needToConvert:
                coinPrice, rawPrice = convertCurrency(coinPrice, currency), round(coinPrice, 2)
            else:
                coinPrice, rawPrice = round(coinPrice, 2), round(coinPrice, 2)
            if display:
                if not firstIteration:
                    for _ in range(8):
                        sys.stdout.write("\033[F")
                        sys.stdout.write("\033[K")
                        sys.stdout.flush()
                print(f"Summary of crypto market at {tickTime.strip()}")
                print(f"Sourced from {source.strip()}")
                print(f"Coin {coinIndex} ({coinType}):")
                print(f"Coin Price: ${coinPrice} {currency}")
                if firstIteration:
                    if positiveMove:
                        print("\033[32m", end="")
                    else:
                        print("\033[31m", end="")
                    print(f"Change (24H): {coinAdjustment}%\033[0m")
                else:
                    if round(coinPrice - lastCoinPrice, 2) > 0:
                        print("\033[32m", end="")
                    elif round(coinPrice - lastCoinPrice, 2) < 0:
                        print("\033[31m", end="")
                    else:
                        print("\033[33m", end="")
                    print(f"Change (Since last check): ${round(coinPrice - lastCoinPrice, 2)}({round(coinAdjustment - lastCoinAdjustment, 4)}%)\033[0m")
                print(f"Market Cap: {coinMarketCap}")
                print(f"Coin Supply: {coinSupply}")
                print(f"Coin Volume (24H): {coin24Volume}")
            else:
                if lastCoinPrice == None or round(coinPrice - lastCoinPrice, 2) != 0:
                    notification.notify(
                            title=coinType,
                            message=f"{f'Increase of' if positiveMove else f'Decrease of'} {f'{coinAdjustment}% in the past 24 hours!' if firstIteration else f'${round(coinPrice - lastCoinPrice, 2)}({round(coinAdjustment - lastCoinAdjustment, 4)}%) since last check!'} Currently sitting at ${coinPrice} {currency}!",
                            app_name='Open Source Crypto Tracker',
                            timeout=tickInterval+2
                        )
                elif round(coinPrice - lastCoinPrice, 2) == 0:
                    notification.notify(
                            title=coinType,
                            message=f"No changes since last check! Currently sitting at ${coinPrice} {currency}!",
                            app_name='Open Source Crypto Tracker',
                            timeout=tickInterval+2
                        )
            firstIteration, lastCoinAdjustment, lastCoinPrice = False, coinAdjustment, rawPrice
            time.sleep(tickInterval)
        except KeyboardInterrupt:
            print("")
            print("Shutting down...")
            exit()
        except Exception as e:
            print("ERROR")
            print(e)
            exit()
