(function (global, factory) {
    typeof exports === 'object' && typeof module !== 'undefined' ? factory(exports) :
    typeof define === 'function' && define.amd ? define(['exports'], factory) :
    (factory((global.d3 = global.d3 || {})));
}(this, (function (exports) { 'use strict';

function constant(x) {
  return function() {
    return x;
  };
}

var ellipseForce = function (padding, innerRepulsion, outerRepulsion) {
  var nodes;
  
  if (typeof padding !== "function") padding = constant(padding == null ? 4 : +padding);
  innerRepulsion = innerRepulsion == null ? 0.5 : +innerRepulsion;
  outerRepulsion = outerRepulsion == null ? 0.5 : +outerRepulsion;

  function force(alpha) {
    var i, j, n = nodes.length,
        // dimensions of this node
        node, myPadding, myW, myH, myX, myY,
        // often used multiples
        myW2, myH2, myWH,
        // dimensions of the other node 
        other, otherPadding, otherW, otherH, otherX, otherY,
        // distance between nodes
        distX, distY,
        // components for the overall result
        forceRatio, dist, gap, repulsion, xComponent, yComponent,
        // computing elliptical force 
        g, g2, x1, y1, x2, y2, d1, d2,
        forceRatio1, forceRatio2,
        // parameters
        myOuterRepulsion = outerRepulsion * 16;

    for (i = 0; i < n; ++i) {
      node = nodes[i];
      myPadding = +padding(node, i, nodes);
      myW = node.rx + myPadding;
      myH = node.ry + myPadding;
      myW2 = myW * myW;
      myH2 = myH * myH;
      myWH = myW * myH;
      myX = node.x + node.vx;
      myY = node.y + node.vy;

      for (j = 0; j < n; ++j) {
          if (j == i) {
              continue;             
          }
          other = nodes[j];
          otherPadding = +padding(other, j, nodes);
          otherW = other.rx + otherPadding;
          otherH = other.ry + otherPadding;
          otherX = other.x + other.vx;
          otherY = other.y + other.vy;
          distX = myX - otherX;
          distY = myY - otherY;
          if (distX == 0 && distY == 0) {
              node.vx += (Math.random() * 4) - 2;
              node.vy += (Math.random() * 4) - 2;  
              continue;            
          } else if (distX == 0) {
              forceRatio = (myH / myW + otherH / otherW) / 2;
              dist = Math.abs(distY);
              gap = dist - myH - otherH;
          } else if (distY == 0) {
              forceRatio = 1;
              dist = abs(distX);
              gap = dist - myW - otherW;
          } else {
              // ellipse is defined as  x^2   y^2
              //                        --- + --- = 1
              //                        w^2   h^2
              // here x,y are points on ellipse's arc. 
              // we have a line going between center points of two ellipses and we want to know
              // the point where it crosses the ellipse's arc. Because we know the line, we
              // know that y = g * x, where    
              g = distY / distX;
              // now the only unknown in ellipse above is x, and thus we can find it by  
              // moving pieces around (pen and paper work). equation becomes: 
              //             w * h
              // x = ---------------------
              //     sqrt(h^2 + g^2 * w^2)

              g2 = g * g;
              x1 = myWH / Math.sqrt(myH2 + g2 * myW2);
              y1 = g * x1;
              // the length of the little bit from the center of ellipse to its margin. 
              // For circle it would be 'r', but for ellipse it varies. 
              d1 = Math.sqrt(x1 * x1 + y1 * y1);
              // Strength of force that this ellipse eminates is modified by ratio of this bit 
              // to the ellipse's width. (It doesn't matter if we use width or height as reference
              // point)  
              force_ratio1 = d1 / myW;
              // And same for the other ellipse:
              x2 = (otherW * otherH) / Math.sqrt(otherH * otherH + g2 * otherW * otherW);
              y2 = g * x2;
              d2 = Math.sqrt(x2 * x2 + y2 * y2);
              force_ratio2 = d2 / otherW;
              // now we can calculate the gap or overlap between two ellipses, and force ratio on 
              // how strongly they should push as average of their force_ratios
              dist = Math.sqrt(distX * distX + distY * distY);
              gap = dist - d2 - d1;
              forceRatio = (forceRatio1 + forceRatio2) / 2;
          }
          xComponent = distX / dist;
          yComponent = distY / dist;
          if (gap < 0) { // force GROWS as gap goes further into negative
              repulsion = Math.min(Math.max(1.0, innerRepulsion * forceRatio * -gap), 5.0);
              node.vx += repulsion * xComponent;
              node.vy += repulsion * yComponent;              
          } else { // force DIMINISHES as gap becomes larger
              repulsion = Math.min(20.0, (forceRatio * myOuterRepulsion * alpha) / gap);
              node.vx += repulsion * xComponent;
              node.vy += repulsion * yComponent;
          }
      }
    }
  }

  force.initialize = function(myNodes) {
    nodes = myNodes;
  };

  force.outerRepulsion = function(myOuterRepulsion) {
    if (arguments.length) {
      outerRepulsion = +myOuterRepulsion;
      return force;
    } else {
      return outerRepulsion;
    }
  };

  force.innerRepulsion = function(myInnerRepulsion) {
    if (arguments.length) {
      innerRepulsion = +myInnerRepulsion;
      return force;
    } else {
      return innerRepulsion;
    }
  };

  force.padding = function(myPadding) {
    if (arguments.length) {
      if (typeof myPadding  === "function") {
        padding = myPadding;
      } else {
        padding = constant(+myPadding);
      }      
      return force;
    } else {
      return padding;
    }
  };


  return force;
};

exports.ellipseForce = ellipseForce;

Object.defineProperty(exports, '__esModule', { value: true });

})));
