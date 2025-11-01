import fs from 'fs'

function getSingleJson() {
  let i = 0
  let filesQuantity = 2

  let arrAllData = []

  do {
    // Read the JSON file
    const rawData = fs.readFileSync(`./gm-${i + 1}-odd.json`, 'utf-8')
    const data = JSON.parse(rawData)

    arrAllData.push(data)

    i++
  } while (i < filesQuantity)

  console.log(arrAllData[20])
  let flattedArr = arrAllData.flat()

  fs.writeFileSync(`./all/gm-all-odd.json`, JSON.stringify(flattedArr, null, 2))
}

getSingleJson()
