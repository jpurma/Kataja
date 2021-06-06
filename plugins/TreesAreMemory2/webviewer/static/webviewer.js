const CONST_NODE = 0
const NEG_FEAT = 1
const POS_FEAT = 2
const NUM_NODE = 3
const FEAT_CHECK = 3

let showWeights = true;
const svg = d3.select("svg");
svg.attr("width", window.innerWidth - 8);
svg.attr("height", window.innerHeight - 16);

let svg_width = svg.attr("width");
let svg_height = svg.attr("height");
let center_x = svg_width / 2;
let center_y = svg_height / 2;

let routeSet = 0;
let route = 0;
let step = 0;
let nodeMap = {};

const graph = {nodes: [], links:[], info:{}};

var accents = [
    [181, 137, 0, 1], // [45, 100, 35], // #b58900 yellow
    [203, 75, 22, 1], //[18, 80, 44], // #cb4b16 orange
    [220, 50, 47, 1], //[1, 71, 52], // #dc322f red
    [211, 54, 130, 1], //[331, 164, 52], // #d33682 magenta
    [108, 113, 196, 1], //[237, 43, 60], // #6c71c4 violet
    [38, 139, 210, 1], //[205, 69, 49], // #268bd2 blue
    [42, 161, 152, 1], //[175, 59, 40], // #2aa198 cyan
    [133, 153, 0, 1] //[68, 100, 30] // #859900 green
];

///////////////////////////////////

// Generic 'get' from api endpoint
const get = (endpoint) => {
        var opts = {
                method: 'GET',
                headers: {}
        };
        return fetch(endpoint, opts)
                .then(response => response.json());
};

const post = (endpoint, data) => {
    var opts = {
        method: 'POST',
        headers: {},
        body: data
    };
    return fetch(endpoint, opts)
        .then(response => response.json());
};


const openNetwork = () => {
    get('/api/net').then(redrawGraph);
}

openNetwork()

svg.append("rect")
    .attr("fill", "none")
    .attr("pointer-events", "all")
    .attr("width", svg_width)
    .attr("height", svg_height)
    .call(d3.zoom()
        .scaleExtent([0.1, 8])
        .on("zoom", zoom));

const g = svg.append("g");
g.attr("class", "node link labels");

var numerate = function () {
    var nodes;

    function force(alpha) {
        for (const nd of nodes) {
            if (nd.type == NUM_NODE) {
                var n = parseInt(nd.id.substr(1));
                var dom_adjust = nd.dom || 0;
                nd.x = 200 + 50 * n;
                nd.y = 200 - 35 * dom_adjust;
            }
        }
    };

    force.initialize = function(myNodes) {
        nodes = myNodes;
    };

    return force;
};

var linkPullForce = d3.forceLink()
    .id(d => d.id)
    .strength(linkForce);

var simulation = d3.forceSimulation()
    .force("link", linkPullForce)
    .force("collide", d3.ellipseForce(10, .7, 0.1))
    .force("numeration", numerate())
    .force("x", d3.forceX(d => {
        if (d.type == 0) {
            return 300;
        } else if (d.type == NEG_FEAT) {
            return 200;
        } else if (d.type == POS_FEAT) {
            return 600;
        } else {
            return d.start_x
        }}).strength(d => {
        if (d.type == NEG_FEAT || d.type == POS_FEAT) {
            return 0.3;
        } else {
            return 0.03;
        }
    }))
    .force("y", d3.forceY(d => {
        if (d.type == 0) {
            return 300;
        } else if (d.type == NEG_FEAT || d.type == POS_FEAT) {
            return 500;
        } else {
            return d.start_y;
        }}).strength(d => 0.1));

let link = g.selectAll("line").data(graph.links, d => d.id);
let node = g.selectAll("ellipse").data(graph.nodes, d => d.id);
let text = g.selectAll("text").data(graph.nodes, d => d.id);

function ticked() {
    link
        .attr("x1", d => d.source.x)
        .attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x)
        .attr("y2", d => d.target.y);
    node
        .attr("cx", d => d.x)
        .attr("cy", d => d.y);
    text
        .attr('transform', d => `translate(${d.x},${d.y})`);
}

function zoom() {
    g.attr("transform", d3.event.transform);
}

function dragstarted(d) {
    if (!d3.event.active) {
        simulation.alphaTarget(0.05).restart();
    }
    d.fx = d.x;
    d.fy = d.y;
}

function dragged(d) {
    d.fx = d3.event.x;
    d.fy = d3.event.y;
}

function dragended(d) {
    if (!d3.event.active) simulation.alphaTarget(0);
    d.fx = null;
    d.fy = null;
}

function selectNode(d) {
    const token = encodeURIComponent(d.id);
    console.log(d)
}

const resizeSvg = function() {
    svg_width = window.innerWidth - 8;
    svg_height = window.innerHeight - 16;

    svg.attr("width", svg_width);
    svg.attr("height", svg_height);
    center_x = svg_width / 2;
    center_y = svg_height / 2;
    simulation.force("x", d3.forceX(center_x).strength(d => 0.5))
        .force("y", d3.forceY(center_y).strength(d => 0.5));
    simulation.alpha(0.1).alphaTarget(0).restart();
}

window.addEventListener('resize', resizeSvg, false);

function fuzz() {
    return Math.random() * 400 - 200
}

function fuzz10() {
    return Math.random() * 30 - 15
}

function nodeStroke(d) {
    if (d.available) {
        return '#eee';
    }
    return nodeFill(d);
}

function nodeFill(d) {
    const rgba = nodeColor(d);
    let a = .25;
    if (d.arg) {
        a = 0.8;
    } else if (d.active) {
        a = 1.0;
    } else if (d.available) {
        a = 0.75;
    } else if (d.used) {
        a = 0.5;
    }
    return `rgba(${rgba[0]}, ${rgba[1]}, ${rgba[2]}, ${a})`;

}

function nodeColor(d) {
    if (d.type == CONST_NODE) {
        if (d.arg) {
            return accents[7]
        } else {
            return accents[0];
        }
    } else if (d.type == NEG_FEAT) {
        return accents[4];
    } else if (d.type == POS_FEAT) {
        return accents[2];
    } else if (d.type == NUM_NODE) {
        return accents[6];
    }
}

function isActive(d) {
    return d.source.active && d.target.active
}

function isUsed(d) {
    return d.source.used && d.target.used
}

function isAvailable(d) {
    return d.source.available && d.target.available
}


function linkColor(d) {
    let rgb = [80, 80, 80];
    if (d.type == 0) {
        rgb = [180, 180, 180];
    } else if (d.type == NEG_FEAT) {
        rgb = accents[4];
    } else if (d.type == POS_FEAT) {
        rgb = accents[2];
    } else if (d.type == FEAT_CHECK) {
        rgb = [220, 139, 210];
    }
    let a = .25;
    if (isActive(d)) {
        //rgb = [128, 0, 0]
        a = 1.0;
    } else if (isAvailable(d)) {
        // rgb = [128, 128, 0]
        a = .6;
    } else if (isUsed(d)) {
        rgb = [0, 0, 0]
        a = .4;
    }
    return `rgba(${rgb[0]}, ${rgb[1]}, ${rgb[2]}, ${a})`;
}

function linkWidth(d) {
    if (isActive(d)) {
        return 4;
    } else if (isAvailable(d)) {
        return 2;
    } else if (isUsed(d)) {
        return 2;
    } else {
        return 1;
    }
}

function linkForce(d) {
    if (d.type == FEAT_CHECK) {
        return 1.0
    }
    if (isActive(d)) {
        return 0.5;
    } else if (isAvailable(d) || isUsed(d)) {
        return 0.1;
    } else {
        return 0;
    }
}


function strokeWidth(d) {
    return 2
    //return d.weight * 10.0;
}

function handleMouseOver() {
    d3.select(this)
        .attr('stroke', d => {
            const c = d3.hsl(nodeColor(d));
            c.l += 0.15;
            return c;
        })
        .attr("stroke-width", d => 3);
}

function handleMouseOut() {
    d3.select(this)
        .attr('stroke', nodeStroke)
        .attr('stroke-width', strokeWidth);
}

function calculatePositions() {
    graph.nodes.forEach(nd => {
        nd.x = fuzz() + center_x;
        if (nd.type == NEG_FEAT || nd.type == POS_FEAT) {
            nd.y = fuzz() / 2 + center_y + 200;
        } else {
            nd.y = fuzz() / 2 + center_y;
        }
        nd.start_x = nd.x;
        nd.start_y = nd.y;
    });
}

function nextTree() {
    routeSet++;
    if (routeSet === graph.routes.length) {
        routeSet = 0;
    }
    route = 0;
    resetRoute();
}

function prevTree() {
    routeSet--;
    if (routeSet === -1) {
        routeSet = graph.routes.length - 1;
    }
    route = 0;
    resetRoute();
}

function nextRoute() {
    route++;
    if (route === graph.routes[routeSet].length) {
        route = 0;
    }
    resetRoute();
}

function prevRoute() {
    route--;
    if (route === -1) {
        route = graph.routes[routeSet].length - 1;
    }
    resetRoute();
}

function nextStep() {
    step++;
    if (step === graph.routes[routeSet][route].length) {
        step = 0;
    }
    updateRoute();
    // animate();
}

function prevStep() {
    step--;
    if (step === -1) {
        step = graph.routes[routeSet][route].length - 1;
    }
    updateRoute();
    // animate();
}

function resetRoute() {
    step = 0
    updateRoute();
}

function markUsed(state, states) {
    let num_node;
    const arg_nums = [];

    for (const argPair of state.arg_ids) {
         num_node = nodeMap[argPair[0]];
         num_node.used = true;
         nodeMap[argPair[1]].used = true;
         arg_nums.push(num_node);
    }
    for (const headPair of state.head_ids) {
         num_node = nodeMap[headPair[0]];
         num_node.used = true;
         if (state.arg_ids.length) {
             for (const arg_num of arg_nums) {
                 if (arg_num.dom >= num_node.dom) {
                     num_node.dom = arg_num.dom + 1;
                 } else {
                     arg_num.dom = num_node.dom - 1;
                 }
             }
         }
         nodeMap[headPair[1]].used = true;
    }
    for (const featTuple of state.checked_features) {
        nodeMap[featTuple[0]].used = true;
        nodeMap[featTuple[1]].used = true;
    }
}

function updateRoute() {
    graph.nodes.forEach(n => {
        n.active = false;
        n.available = false;
        n.used = false;
        n.arg = false;
        n.dom = 0;
    });
    const states = graph.states[routeSet];
    const routes = graph.routes[routeSet];
    if (routes.length) {
            for (let i=0; i<step; i++) {
                markUsed(states[routes[route][i]], states);
            }
            const route_id = routes[route][step];
            const state = states[route_id];
            //console.log('step: ', step, ' route_id: ', route_id);
            const arg_nums = [];
            for (const argPair of state.arg_ids) {
                const num = nodeMap[argPair[0]];
                const arg = nodeMap[argPair[1]];
                arg.active = true;
                num.active = true;
                arg.arg = true;
                num.arg = true;
                arg.available = true;
                num.available = true;
                arg_nums.push(num);
                for (const feat_id of arg.features) {
                    nodeMap[feat_id].available = true;
                }
            }
            for (const headPair of state.head_ids) {
                const num = nodeMap[headPair[0]];
                const head = nodeMap[headPair[1]];
                head.active = true;
                num.active = true;
                head.available = true;
                num.available = true;
                if (state.arg_ids.length) {
                    for (const arg_num of arg_nums) {
                        if (arg_num.dom >= num.dom) {
                            num.dom = arg_num.dom + 1;
                        } else {
                            arg_num.dom = num.dom - 1;
                        }
                    }
                }
                for (const feat_id of head.features) {
                    nodeMap[feat_id].available = true;
                }
            }
            for (const featTuple of state.checked_features) {
                nodeMap[featTuple[0]].active = true;
                nodeMap[featTuple[0]].available = true;
                nodeMap[featTuple[1]].active = true;
                nodeMap[featTuple[1]].available = true;
            }
    }

    link.attr("stroke", linkColor);
    link.attr("stroke-width", linkWidth);
    node.attr("fill", nodeFill);
    node.attr("stroke", nodeStroke);
    updateUICounters();
    simulation.force("link", linkPullForce);
    //animate();
}

function updateUICounters() {
    document.getElementById('tree_n').innerText = `${routeSet + 1}/${graph.routes.length}`;
    const routes = graph.routes[routeSet];
    if (routes.length) {
        document.getElementById('route_n').innerText = `${route + 1}/${routes.length}`;
        document.getElementById('step_n').innerText = `${step + 1}/${routes[route].length}`;
    } else {
        document.getElementById('route_n').innerText = '-';
        document.getElementById('step_n').innerText = '-';
    }
    document.getElementById('state_message').innerText = routes[route] ? graph.states[routeSet][routes[route][step]].msg : '';
}

function animate() {
    simulation.alpha(0.3).alphaTarget(0).restart();
}



// ---------------- update graph starts ------------------

function redrawGraph(data) {
    // map of existing nodes by their id
    nodeMap = graph.nodes.reduce((map, nd) => {
            map[nd.id] = nd;
            return map;
        }, {});

    graph.nodes = data.nodes;
    graph.links = data.links;
    graph.links.forEach(e => {
        e.source = e.start;
        e.target = e.end;
    });
    graph.info = data.info;
    graph.routes = data.routes;
    graph.states = data.states;


    // map of nodes that target the given node id
    const targetMap = graph.links.reduce((m, link) => {
        const start = nodeMap[link.start];
        if (start) {
            if (m && m[link.end]) {
                m[link.end].push(start);
            } else {
                m[link.end] = [start];
            }
        }
        return m;
    }, {});

    calculatePositions();

    link = g.selectAll("line").data(graph.links, d => d.id);

    link.exit().remove();

    link = link.enter().append("line") //d => d.type == CONST_NODE ? "path" : "line")
        .merge(link)
        .attr("stroke-width", linkWidth)
        .attr("stroke", linkColor)

    node = g.selectAll("ellipse").data(graph.nodes, d => d.id);

    node.exit().transition()
        .attr("rx", 0)
        .attr("ry", 0)
        .remove();

    node.attr("x", d => d.x)
        .attr("y", d => d.y);

    node = node.enter().append("ellipse")
        .attr("rx", 0)
        .attr("ry", 0)
        .attr("fill", nodeFill)
        .attr("stroke", nodeStroke)
        .attr("stroke-width", strokeWidth)
        .merge(node)
        .call(d3.drag()
            .on("start", dragstarted)
            .on("drag", dragged)
            .on("end", dragended)
            .clickDistance(6))
        .on("click", selectNode)
        .on("mouseover", handleMouseOver)
        .on("mouseout", handleMouseOut)
        .raise();

    text = g.selectAll("text").data(graph.nodes, d => d.id);

    text.exit().remove();

    text = text.enter().append("text")
        .attr("dy", 2)
        .attr("text-anchor", "middle")
        .text(d => d.id)
        .attr("fill", "#93a1a1;")
        .merge(text)
        .raise();

    graph.nodes.forEach(nd => {
        nd.rx = 36;
        nd.ry = 18;
    });

    nodeMap = graph.nodes.reduce((map, nd) => {
            map[nd.id] = nd;
            return map;
        }, {});

    resetRoute();

    // updating existing/merged new nodes is done last because new texts may have changed the text box size
    // for existing nodes.
    node
        .attr("rx", d => d.rx)
        .attr("ry", d => d.ry)
        .attr("fill", nodeFill)
        .attr("stroke", nodeStroke)
        .attr("stroke-width", strokeWidth);

    link
        .attr("stroke-width", linkWidth)
        .attr("stroke", linkColor)

    // restart animations and graph calculations
    simulation
        .nodes(graph.nodes);
    simulation.force("link")
             .links(graph.links);

    simulation.alpha(0.3).alphaTarget(0).restart();

    simulation
        .on("tick", ticked);
}
// ---------------- update graph ends ------------------
