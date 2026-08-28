// Простой тест подключения к API Wildberries.
// Запуск:  WB_API_KEY="ваш_токен" node test-wb-connection.js
// Требуется Node.js 18 или новее (есть встроенный fetch).

const apiKey = process.env.WB_API_KEY;

if (!apiKey) {
  console.error("Не задан токен. Запустите так:");
  console.error('  WB_API_KEY="ваш_токен" node test-wb-connection.js');
  process.exit(1);
}

function threeDaysAgo() {
  const d = new Date();
  d.setDate(d.getDate() - 3);
  return d.toISOString().slice(0, 10);
}

async function main() {
  const dateFrom = threeDaysAgo();
  console.log(`Запрашиваю продажи с ${dateFrom}...`);

  const res = await fetch(
    `https://statistics-api.wildberries.ru/api/v1/supplier/sales?dateFrom=${dateFrom}`,
    { headers: { Authorization: apiKey } }
  );

  console.log(`HTTP статус: ${res.status}`);

  const text = await res.text();

  if (!res.ok) {
    console.error("Ошибка запроса. Тело ответа:");
    console.error(text);
    process.exit(1);
  }

  let data;
  try {
    data = JSON.parse(text);
  } catch {
    console.error("Ответ не является JSON:");
    console.error(text.slice(0, 500));
    process.exit(1);
  }

  console.log(`Успех! Получено записей: ${Array.isArray(data) ? data.length : "не массив — " + typeof data}`);
  console.log("Первая запись (для проверки структуры):");
  console.log(JSON.stringify(Array.isArray(data) ? data[0] : data, null, 2));
}

main().catch((err) => {
  console.error("Не удалось выполнить запрос:", err.message);
  process.exit(1);
});
