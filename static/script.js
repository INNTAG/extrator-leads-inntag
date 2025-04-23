const dropArea = document.getElementById("drop-area");
const fileInput = document.getElementById("file-input");
const form = document.getElementById("lead-form");
const ctx = document.getElementById("graficoConsumo").getContext("2d");
let chart;

dropArea.addEventListener("click", () => fileInput.click());
fileInput.addEventListener("change", () => handleFile(fileInput.files[0]));
dropArea.addEventListener("dragover", e => { e.preventDefault(); dropArea.style.borderColor = "green"; });
dropArea.addEventListener("dragleave", () => dropArea.style.borderColor = "#007bff");
dropArea.addEventListener("drop", e => {
  e.preventDefault();
  handleFile(e.dataTransfer.files[0]);
});

function handleFile(file) {
  const formData = new FormData();
  formData.append("file", file);
  fetch("/upload", {
    method: "POST",
    body: formData
  })
  .then(r => r.json())
  .then(data => {
    document.getElementById("cidade").value = data.cidade || "";
    document.getElementById("cep").value = data.cep || "";
    document.getElementById("rua").value = data.rua || "";
    document.getElementById("numero").value = data.numero || "";
    document.getElementById("consumo_medio").value = data.consumo_medio || "";
    document.getElementById("cpf").value = data.cpf || "";
    document.getElementById("nome").value = data.nome || "";
    document.getElementById("preview-pdf").src = `/pdf/${data.arquivo}`;

    if (chart) chart.destroy();
    if (data.consumos) {
      const meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'];
      chart = new Chart(ctx, {
        type: "bar",
        data: {
          labels: meses.slice(-data.consumos.length),
          datasets: [{
            label: "Consumo (kWh)",
            data: data.consumos,
            backgroundColor: "#0099b2"
          }]
        },
        options: {
          scales: {
            y: {
              beginAtZero: true,
              ticks: { stepSize: 100 }
            }
          }
        }
      });
    }
  });
}

form.addEventListener("submit", async e => {
  e.preventDefault();
  const data = Object.fromEntries(new FormData(form).entries());
  await fetch("https://hook.us1.make.com/fg9doeumoj2xcb35tjpog3uvwt4oacqd", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  });
  alert("Lead enviado com sucesso!");
});
