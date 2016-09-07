
    var can, ctx, timer, bwidth, bheight, cwidth, cheight, counter, max_count = 0;
    var l1, l2, l3, l4, title = 0;
    var color_i, color_knob, knob_r = 0;
    var draw_tree = true;
    var color_sets = [
    {content: "#202020", paper: "#fff", halfbright: "rgba(255, 255, 255, 0.5)", bright: "#fff"},
    {content: "#3E654D", paper: "#FDF7DF", halfbright: "#FDBD89", bright: "#FAF394"},
    {content: "#073642", paper: "#eee8d5", halfbright: "#839496", bright: "#fdf6e3"}
    ];


    function init() {
        window.onresize = resize_event;
        can = document.getElementById("can");
        ctx = can.getContext("2d");
        l1 = document.getElementById("leaf1");
        l2 = document.getElementById("leaf2");
        l3 = document.getElementById("leaf3");
        l4 = document.getElementById("leaf4");
        title = document.getElementById("main_title");
        color_knob = document.getElementById("color_knob");
        color_knob.onmouseover = knob_hover_enter;
        color_knob.onmouseout = knob_hover_leave;
        color_knob.onclick = knob_click;
        color_i = 0;
        knob_r = 0;
        resize(false);
        max_count = 100;
        counter = 0;
        if (draw_tree) {
            var my_url = window.location.href.toString();
            if (my_url.includes('#') || my_url.includes('.html') || my_url.includes('/documentation')
              || my_url.includes('/about') || my_url.includes('/download') || my_url.includes('/research')) {
              do_draw(100, 130, 1);
            } else {
              timer = setInterval(animate, 1);          
            }
        } else {
            l1.style.opacity = 1;
            l2.style.opacity = 1;
            l3.style.opacity = 1;
            l4.style.opacity = 1;            
        }
    }

    function animate() {
        counter++; 
        var r = easeInOutQuad(counter, 0, 1, max_count);
        var start_x = 100;
        var start_y = 150 - r * 20;
        do_draw(start_x, start_y, r);
        if (counter == max_count) {
            window.clearInterval(timer);
        }
      }

    function do_draw(start_x, start_y, r) {
        var my_bw = r * bwidth;
        var my_bh = r * bheight;
        l1.style.opacity = r;
        l2.style.opacity = r;
        l3.style.opacity = r;
        l4.style.opacity = r;
        ctx.clearRect(0, 0, can.width, can.height, 99);
        ctx.fillStyle = color_sets[color_i].bright;
        title.style.top = (start_y - title.offsetHeight) + "px";
        title.style.left = (start_x - title.offsetWidth / 2 + 20) + "px";
        var endpoint = lbranch(start_x - 5, start_y, my_bw, my_bh);
        l1.style.left = (endpoint.x - l1.offsetWidth / 2) + "px";
        l1.style.top = endpoint.y + "px";
        endpoint = rbranch(start_x + 5, start_y, my_bw, my_bh);            
        var endpoint2 = lbranch(endpoint.x, endpoint.y, my_bw, my_bh);
        l2.style.left = (endpoint2.x - l2.offsetWidth / 2) + "px";
        l2.style.top = endpoint2.y + "px";
        endpoint = rbranch(endpoint.x, endpoint.y, my_bw, my_bh);
        endpoint2 = lbranch(endpoint.x, endpoint.y, my_bw, my_bh);
        l3.style.left = (endpoint2.x - l3.offsetWidth / 2) + "px";
        l3.style.top = endpoint2.y + "px";
        endpoint = rbranch(endpoint.x, endpoint.y, my_bw, my_bh);
        l4.style.left = (endpoint.x - l4.offsetWidth / 2) + "px";
        l4.style.top = endpoint.y + "px";
    }

    function lbranch(sx, sy, bwidth, bheight) {
        var ex = sx - bwidth;
        var ey = sy + bheight;
        branch(sx, sy, ex, ey);
        return {x:ex, y:ey};
    }

    function rbranch(sx, sy, bwidth, bheight) {
        var ex = sx + bwidth;
        var ey = sy + bheight;
        branch(sx, sy, ex, ey);
        return {x:ex, y:ey};
    }

    function branch(sx, sy, ex, ey) {
        ctx.beginPath();
        var skew = 0.5
        var skewed = (ey - sy) * skew;
        ctx.moveTo(sx, sy);            
        ctx.bezierCurveTo(sx, sy + skewed + 3, ex, ey - skewed, ex, ey);
        ctx.bezierCurveTo(ex, ey - skewed - 3, sx, sy + skewed, sx, sy);
        ctx.fill()
    }

    function easeInOutQuad(t, b, c, d) {
        t /= d/2;
        if (t < 1) return c/2*t*t + b;
        t--;
        return -c/2 * (t*(t-2) - 1) + b;
    };

    function knob_hover_enter() {
      color_knob.style.transform = 'rotate(' + (knob_r + 10) + 'deg)';
    }
    
    function knob_hover_leave() {
      color_knob.style.transform = 'rotate(' + knob_r + 'deg)';
    }

    function knob_click() {
      knob_r += 360 / color_sets.length;
      color_knob.style.transform = 'rotate(' + knob_r + 'deg)';
      color_i++;
      if (color_sets.length == color_i) color_i = 0;
      update_colors(color_sets[color_i]);
    }

    function update_colors(p) {
      var sel = document.querySelector('.sidebar');
      sel.style.backgroundColor = p.content;
      sel.style.color = p.halfbright;
      title.style.color = p.bright;  
      var sel = document.querySelectorAll('.sidebar a');
      var i;
      for (i = 0; i < sel.length; i++) {
          sel[i].style.color = p.bright;
      }
      can.style.backgroundColor = p.content;
      sel = document.querySelectorAll('.related-posts li a:hover'); // .content a, 
      for (i = 0; i < sel.length; i++) {
          sel[i].style.color = p.content;
      }
      sel = document.querySelector('body');
      sel.style.backgroundColor = p.paper;
      sel.style.color = p.content;
      sel = document.querySelectorAll('h1, h2, h3, h4, h5, h6, strong');
      for (i = 0; i < sel.length; i++) {
          sel[i].style.color = p.content;
      }
      color_knob.style.color = p.bright;
      color_knob.style.borderColor = p.halfbright;
      do_draw(100, 130, 1);
    }

    function resize_event() {
        resize(true);
    }

    function resize(skip_animation) {
        if (window.innerWidth < 768) {
            draw_tree = false;
        } else if (window.innerWidth < 928) {
            draw_tree = true;
            cwidth = 240;
            cheight = 260;
            bwidth = 35;
            bheight = 30;
        } else {
            draw_tree = true;
            cwidth = 300;
            cheight = 300;
            bwidth = 55;
            bheight = 40;
        }
        if (draw_tree) {
            if (window.devicePixelRatio == 2) {
                can.style.width = cwidth + "px";
                can.style.height = cheight + "px";
                can.width = cwidth * 2; 
                can.height = cheight * 2;
                ctx.scale(2, 2);
            } else {
                can.style.width = cwidth + "px";
                can.style.height = cheight + "px";
                can.width = cwidth; 
                can.height = cheight;
            }            
            if (skip_animation) {
                do_draw(100, 130, 1);
            }            
        }
    }
