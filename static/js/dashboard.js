document.getElementById("uploadForm").addEventListener("submit", async (e) => {
    e.preventDefault();

    const formData = new FormData(e.target);
    const res = await fetch("/api/upload", { method: "POST", body: formData });
    const data = await res.json();

    if (!data.chart_data) {
        document.getElementById("response").innerHTML = `<p style="color:red;">Error generating forecast.</p>`;
        return;
    }

    document.getElementById("response").innerHTML = `
        <p style="color:#00C6FF;font-weight:600;">${data.message}</p>
        <a href="/download/${formData.get('target_col')}" class="btn">⬇️ Download Forecast CSV</a>
    `;

    const records = data.chart_data;
    const dateCol = data.date_col;
    const yCol = data.target_col;

    const dates = records.map(r => r[dateCol]);
    const forecast = records.map(r => r[yCol]);
    const upper = records.map(r => r[yCol + "_upper"] || null);
    const lower = records.map(r => r[yCol + "_lower"] || null);

    const figData = [
        {
            x: dates,
            y: forecast,
            mode: 'lines',
            name: 'Forecast',
            line: { color: '#00C6FF', width: 3 }
        },
        {
            x: dates,
            y: upper,
            mode: 'lines',
            name: 'Upper Bound',
            line: { color: '#AAAAAA', dash: 'dot' }
        },
        {
            x: dates,
            y: lower,
            mode: 'lines',
            name: 'Lower Bound',
            line: { color: '#AAAAAA', dash: 'dot' }
        }
    ];

    const layout = {
        title: { text: 'Sales Forecast with Confidence Bounds', font: { color: '#FFFFFF' } },
        paper_bgcolor: '#000000',
        plot_bgcolor: '#000000',
        font: { color: '#FFFFFF' },
        xaxis: { title: 'Date' },
        yaxis: { title: 'Value' },
        legend: { font: { color: '#FFFFFF' } }
    };

    Plotly.newPlot('forecastChart', figData, layout, {responsive: true});
});
