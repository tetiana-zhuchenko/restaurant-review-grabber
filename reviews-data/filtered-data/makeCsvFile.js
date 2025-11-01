import fs from 'fs'

function prepareJsonForCsvFile() {
  const rawReviews = fs.readFileSync(
    './all/reviews-main-filtered.json',
    'utf-8'
  )
  const reviews = JSON.parse(rawReviews)

  const filteredByRating = reviews.filter((r) => {
    return r.rating !== 4 && r.rating !== 3
  })

  const makeBinaryRating = filteredByRating.map((i) => {
    if (i.rating === 1 || i.rating === 2) {
      return {
        Review: i.text,
        Liked: 0,
      }
    } else if (i.rating === 5) {
      return {
        Review: i.text,
        Liked: 1,
      }
    }
  })

  fs.writeFileSync(
    `./all/reviews-for-csv-making.json`,
    JSON.stringify(makeBinaryRating, null, 2)
  )
}

// prepareJsonForCsvFile()

function jsonToCsv() {
  const jsonData = fs.readFileSync('./all/reviews-for-csv-making.json', 'utf-8')
  if (!jsonData.length) return ''

  const parsedData = JSON.parse(jsonData)
  const headers = Object.keys(parsedData[0])

  const csvContent = [
    headers.join(','),
    ...parsedData.map((row) =>
      headers
        .map((header) => {
          let cell = row[header]

          // Якщо це число - повертаємо як число (без лапок)
          if (typeof cell === 'number') {
            return cell // Повертаємо число як є (0 або 1)
          }

          // Для null/undefined повертаємо порожній рядок
          if (cell === null || cell === undefined) {
            return ''
          }

          // Для текстових полів
          cell = String(cell)

          // Екранування лапок в тексті
          if (cell.includes('"')) {
            cell = cell.replace(/"/g, '""')
          }

          // Обгортання тексту в лапки якщо містить спецсимволи
          if (cell.includes(',') || cell.includes('"') || cell.includes('\n')) {
            cell = `"${cell}"`
          }

          return cell
        })
        .join(',')
    ),
  ].join('\n')

  fs.writeFileSync('./all/reviews.csv', csvContent, { encoding: 'utf-8' })
}

jsonToCsv()
