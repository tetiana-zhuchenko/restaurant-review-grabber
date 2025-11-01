import fs from 'fs'

function filterDuplicates() {
  let i = 0
  let filesQuantity = 2
  do {
    // Read the JSON file
    const rawData = fs.readFileSync(`./gm-${i + 1}.json`, 'utf-8')
    const data = JSON.parse(rawData)

    // Filter to keep only elements with odd indices (1, 3, 5, ...)
    const oddElements = data.filter((_, index) => index % 2 === 1)

    // Write the new JSON file
    fs.writeFileSync(
      `./filtered-data/gm-${i + 1}-odd.json`,
      JSON.stringify(oddElements, null, 2)
    )

    console.log('Created gm-1-odd.json with odd-index elements')
    i++
  } while (i < filesQuantity)
}

filterDuplicates()
