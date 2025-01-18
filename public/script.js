// Timeout object for debouncing in interactive searches
let timeout = null;

const copyToClipboard = async (event) => {
    try {
        await navigator.clipboard.writeText(event.target.textContent.trim());
    } catch (error) {
        console.error("Failed to copy to clipboard:", error);
    }
};

function addAlternatives(ean) {
    alternative = document.getElementById('ean')
    fetch(`/api/add/alternative/${encodeURIComponent(ean)}/${alternative.value}`)
        .then(response => {
            if (response.status === 200) {
                alternative.value = "";
            } else {
                console.error("Failed to add alternative:", response);
            }
        })
}

function fillEanField(ean) {
    document.getElementById('ean').value = ean;
    document.getElementById('productSearchResults').innerHTML = '';
}

function searchTargetProductPage(ean) {
    return [`/view/product/${ean}`, null];
}

function searchTargetFillForm(ean) {
    return [`#`, function() { fillEanField(ean); return false; }];
}


function performLiveSearch(query, target) {
    clearTimeout(timeout);

    if (query.length > 1) {
        timeout = setTimeout(() => {
            fetch(`/api/search/${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(data => {
                    const resultsContainer = document.getElementById('productSearchResults')
                    resultsContainer.innerHTML = '';

                    data.results.forEach(result => {
                        var a = document.createElement('a');
                        a.classList = 'list-group-item list-group-item-action'
                        var [link, action] = target(result.ean_id);
                        a.href = link;
                        a.onclick = action;

                        var h5 = document.createElement('h5');
                        h5.className = 'mb-1';
                        h5.textContent = result.name;
                        a.appendChild(h5);

                        var p = document.createElement('p');
                        p.className = 'mb-1';
                        p.textContent = result.description ? result.description.length > 128 ? result.description.slice(0,128) : result.description : "";
                        a.appendChild(p);

                        var small_bottom = document.createElement('small');
                        small_bottom.textContent = result.ean_id;
                        a.appendChild(small_bottom);

                        resultsContainer.appendChild(a);
                    });
                });
        }, 200);
    } else {
        const resultsContainer = document.getElementById('productSearchResults')
        resultsContainer.innerHTML = '';
    }
}

if (document.getElementById('priceChart')) {
    product_ean = document.location.pathname.substring(document.location.pathname.lastIndexOf('/') + 1);

    chart = document.getElementById('priceChart');
    bounds = chart.getBoundingClientRect();

    var margin = {top: 0, right: 0, bottom: 30, left: 30},
        width = bounds.width - margin.left - margin.right,
        height = 400 - margin.top - margin.bottom;

    var svg = d3.select('#priceChart')
        .append("svg")
            .attr('width', width + margin.left + margin.right)
            .attr('height', height + margin.top + margin.bottom)
        .append("g")
            .attr("tranform", "translate(" + margin.left + "," + margin.top + ")");

    fetch(`/api/prices/${encodeURIComponent(product_ean)}`)
        .then(response => response.json())
        .then(payload => {
            // Data should be [{"group": group, "x": x, "y": y}]

            var data = payload.results;

            const x = d3.scaleTime()
                .domain(d3.extent(data, d => d3.isoParse(d.x)))
                .range([0, width]);
            svg.append("g")
                .attr("transform", `translate(0, ${height})`)
                .call(d3.axisBottom(x)
                    .ticks(d3.timeDay)
                    .tickFormat((d, i) => (d.getDay() === 1 ? d3.timeFormat("%d.%m.%y")(d) : ""))
                );
            const y = d3.scaleLinear()
                .domain( [ 0, d3.max(data, d => d.y)*1.2 ])
                .range([height, 0]);
            svg.append("g")
                .call(d3.axisRight(y));

            const color = d3.scaleOrdinal(d3.schemeCategory10);

            const line = d3.line()
                //.curve(d3.curveBasis) // Makes the line smooth
                .x(d => x(d3.isoParse(d.x)))
                .y(d => y(d.y));


            // Group data by their store
            let groupedData = {};
            
            data.forEach(item => {
                if (!groupedData[item.group.name]){
                    groupedData[item.group.name] = [];
                }
                groupedData[item.group.name].push(item);
            })

            const nestedData = Object.entries(groupedData);
            const keys = Object.keys(groupedData);

            // Draw the line
            svg.selectAll(".line")
                .data(nestedData)
                .enter().append("path")
                .attr("fill", "none")
                .attr("stroke", d => color(d[0]))
                .attr("stroke-width", 1.5)
                .attr("d", d => line(d[1]));

            // Draw the points
            svg.selectAll(".point")
                .data(data)
                .enter().append("circle")
                .attr("cx", d => x(d3.isoParse(d.x)))
                .attr("cy", d => y(d.y))
                .attr("r", 3)
                .attr("fill", d => color(d.group.name))
                .append("title")
                .text(d => `${d3.timeFormat("%d.%m.%y")(d3.isoParse(d.x))}: ${d.y} €`);

            // Add Legend
            svg.selectAll("legenddots")
                .data(keys)
                .enter()
                .append("circle")
                    .attr("cx", 35)
                    .attr("cy", function(d,i) {return 10 + i*25})
                    .attr("r", 5)
                    .style("fill", function(d) {return color(d)})
                
            svg.selectAll("legendlabels")
                .data(keys)
                .enter()
                .append("text")
                    .attr("x", 42)
                    .attr("y", function(d,i) {return 15 + i*25})
                    .style("fill", function(d) {return color(d)})
                    .text(function(d) {return d})
                    .attr("text-anchor", "left")
                    .style("alignment-baseline", "middle")

        });
}

if (document.getElementById('productSearch')) {
    document.getElementById('productSearch')
        .addEventListener('keyup', function() {performLiveSearch(this.value, searchTargetProductPage)});
} else if (document.getElementsByClassName('productSearch')) {
    document.getElementsByClassName('productSearch').item(0)
        .addEventListener('keyup', function() {performLiveSearch(this.value, searchTargetFillForm)});
}
