document.addEventListener('DOMContentLoaded', function() {
    // Elementos da interface
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('file-input');
    const fileInfo = document.getElementById('file-info');
    const fileName = document.getElementById('file-name');
    const fileSize = document.getElementById('file-size');
    const removeFile = document.getElementById('remove-file');
    const loading = document.getElementById('loading');
    const dataSection = document.getElementById('data-section');
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabPanes = document.querySelectorAll('.tab-pane');
    const newUploadBtn = document.getElementById('new-upload');
    const sendDataBtn = document.getElementById('send-data');
    const notification = document.getElementById('notification');
    const notificationMessage = document.querySelector('.notification-message');
    const notificationClose = document.querySelector('.notification-close');
    
    // Variáveis para armazenar dados
    let extractedData = null;
    let uploadedFile = null;
    
    // Configuração do upload de arquivos
    uploadArea.addEventListener('click', () => fileInput.click());
    
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('active');
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('active');
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('active');
        
        if (e.dataTransfer.files.length) {
            handleFile(e.dataTransfer.files[0]);
        }
    });
    
    fileInput.addEventListener('change', () => {
        if (fileInput.files.length) {
            handleFile(fileInput.files[0]);
        }
    });
    
    removeFile.addEventListener('click', resetUpload);
    
    // Função para processar o arquivo
    function handleFile(file) {
        // Verificar se é um PDF
        if (file.type !== 'application/pdf') {
            showNotification('Apenas arquivos PDF são aceitos.', 'error');
            return;
        }
        
        uploadedFile = file;
        
        // Mostrar informações do arquivo
        fileName.textContent = file.name;
        fileSize.textContent = formatFileSize(file.size);
        fileInfo.style.display = 'flex';
        uploadArea.style.display = 'none';
        
        // Enviar arquivo para processamento
        uploadFile(file);
    }
    
    // Função para enviar o arquivo para o servidor
    function uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        loading.style.display = 'block';
        fileInfo.style.display = 'none';
        
        fetch('/extract', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            loading.style.display = 'none';
            
            if (data.success) {
                extractedData = data.data;
                populateClientData(extractedData.client_data);
                populateConsumptionData(extractedData.consumption_history, extractedData.avg_consumption);
                dataSection.style.display = 'block';
                showNotification('Dados extraídos com sucesso!', 'success');
            } else {
                fileInfo.style.display = 'flex';
                showNotification('Erro ao processar o arquivo: ' + data.error, 'error');
            }
        })
        .catch(error => {
            loading.style.display = 'none';
            fileInfo.style.display = 'flex';
            showNotification('Erro ao processar o arquivo: ' + error.message, 'error');
        });
    }
    
    // Função para preencher os dados do cliente no formulário
    function populateClientData(clientData) {
        document.getElementById('name').value = clientData.name || '';
        document.getElementById('cpf').value = clientData.cpf || '';
        document.getElementById('address').value = clientData.address || '';
        document.getElementById('neighborhood').value = clientData.neighborhood || '';
        document.getElementById('cep').value = clientData.cep || '';
        document.getElementById('city').value = clientData.city || '';
        document.getElementById('state').value = clientData.state || '';
        document.getElementById('email').value = clientData.email || '';
        document.getElementById('phone').value = clientData.phone || '';
    }
    
    // Função para preencher os dados de consumo
    function populateConsumptionData(consumptionHistory, avgConsumption) {
        // Atualizar média de consumo
        document.getElementById('avg-consumption').textContent = `${avgConsumption} kWh`;
        
        // Preencher tabela de consumo
        const tableBody = document.getElementById('consumption-table-body');
        tableBody.innerHTML = '';
        
        consumptionHistory.forEach(item => {
            const row = document.createElement('tr');
            
            const monthCell = document.createElement('td');
            monthCell.textContent = `${item.month_abbr}/${item.year}`;
            row.appendChild(monthCell);
            
            const consumptionCell = document.createElement('td');
            consumptionCell.textContent = `${item.consumption} kWh`;
            row.appendChild(consumptionCell);
            
            const daysCell = document.createElement('td');
            daysCell.textContent = item.days;
            row.appendChild(daysCell);
            
            tableBody.appendChild(row);
        });
        
        // Criar gráfico de consumo
        createConsumptionChart(consumptionHistory);
    }
    
    // Função para criar o gráfico de consumo
    function createConsumptionChart(consumptionHistory) {
        const ctx = document.getElementById('consumption-chart').getContext('2d');
        
        // Inverter a ordem para mostrar do mais antigo para o mais recente
        const chartData = [...consumptionHistory].reverse();
        
        // Extrair labels e dados
        const labels = chartData.map(item => `${item.month_abbr}/${item.year}`);
        const data = chartData.map(item => item.consumption);
        
        // Destruir gráfico existente se houver
        if (window.consumptionChart) {
            window.consumptionChart.destroy();
        }
        
        // Criar novo gráfico
        window.consumptionChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Consumo (kWh)',
                    data: data,
                    backgroundColor: 'rgba(227, 6, 19, 0.7)',
                    borderColor: 'rgba(227, 6, 19, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Consumo (kWh)'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Mês/Ano'
                        }
                    }
                }
            }
        });
    }
    
    // Função para resetar o upload
    function resetUpload() {
        fileInput.value = '';
        fileInfo.style.display = 'none';
        uploadArea.style.display = 'block';
        uploadedFile = null;
    }
    
    // Manipulação das abas
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Remover classe active de todas as abas
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabPanes.forEach(pane => pane.classList.remove('active'));
            
            // Adicionar classe active na aba clicada
            button.classList.add('active');
            document.getElementById(button.dataset.tab).classList.add('active');
        });
    });
    
    // Botão para novo upload
    newUploadBtn.addEventListener('click', () => {
        resetUpload();
        dataSection.style.display = 'none';
        extractedData = null;
    });
    
    // Botão para enviar dados
    sendDataBtn.addEventListener('click', () => {
        if (!extractedData) {
            showNotification('Nenhum dado para enviar.', 'error');
            return;
        }
        
        // Coletar dados atualizados do formulário
        const updatedClientData = {
            name: document.getElementById('name').value,
            cpf: document.getElementById('cpf').value,
            address: document.getElementById('address').value,
            neighborhood: document.getElementById('neighborhood').value,
            cep: document.getElementById('cep').value,
            city: document.getElementById('city').value,
            state: document.getElementById('state').value,
            email: document.getElementById('email').value,
            phone: document.getElementById('phone').value
        };
        
        // Atualizar dados extraídos com os dados do formulário
        extractedData.client_data = updatedClientData;
        
        // Enviar dados para o webhook
        sendDataToWebhook(extractedData);
    });
    
    // Função para enviar dados para o webhook
    function sendDataToWebhook(data) {
        fetch('/send-webhook', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                showNotification('Dados enviados com sucesso!', 'success');
            } else {
                showNotification('Erro ao enviar dados: ' + result.error, 'error');
            }
        })
        .catch(error => {
            showNotification('Erro ao enviar dados: ' + error.message, 'error');
        });
    }
    
    // Função para mostrar notificação
    function showNotification(message, type) {
        notificationMessage.textContent = message;
        notification.className = 'notification ' + type;
        notification.classList.add('show');
        
        // Esconder notificação após 5 segundos
        setTimeout(() => {
            notification.classList.remove('show');
        }, 5000);
    }
    
    // Fechar notificação
    notificationClose.addEventListener('click', () => {
        notification.classList.remove('show');
    });
    
    // Função para formatar o tamanho do arquivo
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
});
