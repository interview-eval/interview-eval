# temp_data.py
MATH_GEO_LEVEL_2 = [
    {
        "initial_question": 'In right triangle $ABC$, shown below, $cos{B}=frac{6}{10}$.  What is $tan{C}$?\n\n[asy]\ndraw((0,0)--(10,0)--(3.6,4.8)--cycle,black+linewidth(1));\ndraw(rightanglemark((0,0),(3.6,4.8),(10,0),20),black+linewidth(1));\nlabel("$C$",(10,0),E);\nlabel("$A$",(3.6,4.8),N);\nlabel("$B$",(0,0),W);\nlabel("10",(0,0)--(10,0),S);\n[/asy]',
        "level": "Level 2",
        "answer": "frac34",
        "solution": "Since $cos{B}=frac{6}{10}$, and the length of the hypotenuse is $BC=10$, $AB=6$.  Then, from the Pythagorean Theorem, we have begin{align*}AB^2+AC^2&=BC^2  Rightarrowqquad{AC}&=sqrt{BC^2-AB^2}  &=sqrt{10^2-6^2}  &=sqrt{64}  &=8.end{align*}Therefore, $tan{C}=frac{AB}{AC}=frac{6}{8} = boxed{frac34}$.",
    },
    {
        "initial_question": 'The sides of triangle $PQR$ are tangent to a circle with center $C$ as shown. Given that $\angle PQR = 63^\circ$ and $\angle QPR = 59^\circ$, find $\angle QRC$, in degrees. [asy] unitsize(1.0 cm); pair Q, P, R, C; Q = (2.43,3.46); P = (0,0); R = (4.43,0); C = incenter(Q,P,R); draw(Q--P--R--cycle); draw(incircle(Q,P,R)); draw(R--C); label("$Q$", Q, N); label("$P$", P, SW); label("$R$", R, SE); label("$C$", C, N); [/asy]',
        "level": "Level 2",
        "answer": "29^\circ",
        "solution": "The circle with center $C$ is the incircle of $triangle PQR$. So, any segment from a vertex of the triangle to $C$ is an angle bisector. The sum of the measures of the internal angles of a triangle is $180^\circ$, so \begin{align*} \angle QRP &= 180^\circ - \angle PQR - \angle QPR \\ &= 180^\circ - 63^\circ - 59^\circ\\ &= 58^\circ. \end{align*}Since $\overline{RC}$ bisects $\angle QRP$, we have $\angle QRC = \frac{58^\circ}{2} = boxed{29^\circ}$.",
    },
    {
        "initial_question": "Compute $tan 3825^\circ$.",
        "level": "Level 2",
        "answer": "1",
        "solution": 'Rotating $360^\circ$ is the same as doing nothing, so rotating $3825^\circ$ is the same as rotating $3825^\circ - 10\cdot 360^\circ = 225^\circ$. Therefore, we have $tan 3825^\circ = tan (3825^\circ - 10\cdot 360^\circ) = tan 225^\circ$. Let $P$ be the point on the unit circle that is $225^\circ$ counterclockwise from $(1,0)$, and let $D$ be the foot of the altitude from $P$ to the $x$-axis, as shown below. [asy] pair A,C,P,O,D; draw((0,-1.2)--(0,1.2),p=black+1.2bp,Arrows(0.15cm)); draw((-1.2,0)--(1.2,0),p=black+1.2bp,Arrows(0.15cm)); A = (1,0); O= (0,0); label("$x$",(1.2,0),SE); label("$y$",(0,1.2),NE); P = rotate(225)*A; D = foot(P,A,-A); draw(O--P--D); draw(rightanglemark(O,D,P,2)); draw(Circle(O,1)); label("$O$",O,NE); label("$P$",P,SW); //label("$A$",A,SE); label("$D$",D,N); [/asy] Triangle $POD$ is a 45-45-90 triangle, so $DO = DP = \frac{\sqrt{2}}{2}$. Therefore, the coordinates of $P$ are $\left(-\frac{\sqrt{2}}{2}, -\frac{\sqrt{2}}{2}\right)$, so $tan 3825^\circ = tan 225^\circ = \frac{\sin 225^\circ}{\cos 225^\circ} = \frac{-\sqrt{2}/2}{-\sqrt{2}/2} = boxed{1}$.',
    },
]
MATH_GEO_LEVEL_3 = [
    {
        "initial_question": "A triangle with sides $3a-1$, $a^2 + 1$ and $a^2 + 2$ has a perimeter of 16 units. What is the number of square units in the area of the triangle?",
        "level": "Level 3",
        "type": "Geometry",
        "answer": "12 units",
        "solution": 'Sum $3a-1$, $a^2+1$, and $a^2+2$ to find $2a^2+3a+2=16$.  Subtract 16 from both sides and factor the left-hand side to find $(2a+7)(a-2)=0implies a=-7/2$ or $a=2$.  Discarding the negative solution, we substitute $a=2$ into $3a-1$, $a^2+1$, and $a^2+2$ to find that the side lengths of the triangle are 5, 5, and 6 units.  Draw a perpendicular from the 6-unit side to the opposite vertex to divide the triangle into two congruent right triangles (see figure).  The height of the triangle is $sqrt{5^2-3^2}=4$ units, so the area of the triangle is $frac{1}{2}(6)(4)=boxed{12text{ square units}}$.\n\n[asy]\nimport olympiad;\nsize(150);\ndefaultpen(linewidth(0.8)+fontsize(10));\npair A=(0,0), B=(6,0), C=(3,4);\ndraw(A--B--C--cycle);\ndraw(C--(A+B)/2,linetype("2 3"));\nlabel("5",(A+C)/2,unit((-4,3)));\nlabel("3",B/4,S);\ndraw("6",shift((0,-0.6))*(A--B),Bars(5));\ndraw(rightanglemark(A,(A+B)/2,C));[/asy]',
    },
    {
        "initial_question": 'Find the number of square units in the area of the triangle. [asy]size(125); draw( (-10,-2) -- (2,10), Arrows); draw( (0,-2)-- (0,10) ,Arrows); draw( (5,0) -- (-10,0),Arrows); label("$l$",(2,10), NE); label("$x$", (5,0) , E); label("$y$", (0,-2) , S); filldraw( (-8,0) -- (0,8) -- (0,0) -- cycle, lightgray); dot( (-2, 6)); dot( (-6, 2)); label( "(-2, 6)", (-2, 6), W, fontsize(10)); label( "(-6, 2)", (-6, 2), W, fontsize(10)); [/asy]',
        "level": "Level 3",
        "type": "Geometry",
        "answer": "32 square units",
        "solution": "We first notice that the vertical and horizontal distances between the two points are both $4$, so the slope of the line which the two points are on must be $1$. We now find the length of the legs of the triangle. Since the slope of the line is one, we can add $2$ to both the $x$ and $y$-coordinates of $(-2,6)$ and get that the line passes through $(0,8)$. Similarly, we can subtract $2$ from the $x$ and $y$-coordinates of $(-6,2)$ to find that it passes through $(-8,0)$. We now have a right triangle with legs of length $8$, so its area is $\frac{1}{2}bh=\frac{1}{2}(8)(8)=boxed{32}$ square units.",
    },
    {
        "initial_question": "A two-gallon container had all of its dimensions tripled. How many gallons does the new container hold?",
        "level": "Level 3",
        "type": "Geometry",
        "answer": "54 gallons",
        "solution": "Suppose that our two-gallon container is in the shape of a rectangular prism. If we triple the length, the volume triples. Tripling the width or the height gives us the same result. Therefore, tripling all of the dimensions increases the volume by a factor of $3\cdot 3 \cdot 3 = 27$. The new container can hold $2 times 27 = boxed{54}$ gallons.",
    },
]

MATH_GEO_LEVEL_4 = [
    {
        "initial_question": "A sphere is inscribed inside a hemisphere of radius 2.  What is the volume of this sphere?",
        "level": "Level 4",
        "type": "Geometry",
        "answer": "frac43pi",
        "solution": '[asy]\n\nsize(110); dotfactor=4; pen dps=linewidth(0.7)+fontsize(10); defaultpen(dps);\ndraw(scale(1,.2)*arc((0,0),1,0,180),dashed);\ndraw(scale(1,.2)*arc((0,0),1,180,360));\ndraw(Arc((0,0),1,0,180));\n\ndraw(Circle((0,.5),.5),heavycyan);\ndraw(scale(1,.2)*arc((0,2.5),.5,0,180),dashed+heavycyan);\ndraw(scale(1,.2)*arc((0,2.5),.5,180,360),heavycyan);\n\ndot((0,0)); dot((0,1));\nlabel("$B$",(0,0),SW); label("$A$",(0,1),NE);\n\n[/asy]\n\nLet $A$ be the point on the hemisphere where the top of the hemisphere touches the sphere, and let $B$ be the point on the hemisphere where the base of the hemisphere touches the sphere.  $AB$ is a diameter of the sphere and a radius of the hemisphere.  Thus, the diameter of the sphere is 2, so the radius of the sphere is 1 and the volume of the sphere is $frac{4}{3}pi (1^3)=boxed{frac{4}{3}pi}$.',
    },
    {
        "initial_question": "A right pyramid has a square base with perimeter 24 inches. Its apex is 9 inches from each of the other vertices. What is the height of the pyramid from its peak to the center of its square base, in inches?",
        "level": "Level 4",
        "type": "Geometry",
        "answer": "3\sqrt{7} inches",
        "solution": '[asy] import three; triple A = (0,0,0); triple B = (1,0,0); triple C = (1,1,0); triple D = (0,1,0); triple P = (0.5,0.5,1); draw(B--C--D--P--B); draw(P--C); draw(B--A--D,dashed); draw(P--A,dashed); label("$A$",A,NW); label("$B$",B,W); label("$C$",C,S); label("$D$",D,E); label("$P$",P,N); triple F= (0.5,0.5,0); label("$F$",F,S); triple M=(B+C)/2; draw(P--F--B,dashed); [/asy] Let $F$ be the center of the square base. Since the pyramid is a right pyramid, triangle $PFB$ is a right triangle. The perimeter of the base of the pyramid is 24 inches, so the length of each side of the base is $6$ inches. Since $F$ is the center of the base, $FB$ is half the diagonal of the base, or $(6\sqrt{2})/2 = 3\sqrt{2}$ inches. Applying the Pythagorean Theorem to triangle $PFB$ gives \[PF = \sqrt{PB^2 - FB^2} = \sqrt{81 - 18} = \sqrt{63} = boxed{3\sqrt{7}} text{ inches}.\]',
    },
    {
        "initial_question": "What is the diameter of the circle inscribed in triangle $ABC$ if $AB = 11,$ $AC=6,$ and $BC=7$? Express your answer in simplest radical form.",
        "level": "Level 4",
        "type": "Geometry",
        "answer": "\sqrt{10}",
        "solution": "Let $d$ be the diameter of the inscribed circle, and let $r$ be the radius of the inscribed circle. Let $s$ be the semiperimeter of the triangle, that is, $s=\frac{AB+AC+BC}{2}=12$. Let $K$ denote the area of $triangle ABC$. Heron's formula tells us that \begin{align*} K &= \sqrt{s(s-AB)(s-AC)(s-BC)} \\ &= \sqrt{12\cdot 1\cdot 6\cdot 5} \\ &= \sqrt{6^2\cdot 10} \\ &= 6\sqrt{10}. \end{align*}The area of a triangle is equal to its semiperimeter multiplied by the radius of its inscribed circle ($K=rs$), so we have $$6\sqrt{10} = r\cdot 12,$$which yields the radius $r=\frac {\sqrt{10}}{2}$. This yields the diameter $d = boxed{\sqrt{10}}$.",
    },
]

MATH_GEO_LEVEL_5 = [
    {
        "initial_question": 'A cone has a volume of $12288\pi$ cubic inches and the vertex angle of the vertical cross section is 60 degrees. What is the height of the cone? Express your answer as a decimal to the nearest tenth. [asy] import markers; size(150); import geometry; draw(scale(1,.2)*arc((0,0),1,0,180),dashed); draw(scale(1,.2)*arc((0,0),1,180,360)); draw((-1,0)--(0,sqrt(3))--(1,0)); //draw(arc(ellipse((2.5,0),1,0.2),0,180),dashed); draw(shift((2.5,0))*scale(1,.2)*arc((0,0),1,0,180),dashed); draw((1.5,0)--(2.5,sqrt(3))--(3.5,0)--cycle); //line a = line((2.5,sqrt(3)),(1.5,0)); //line b = line((2.5,sqrt(3)),(3.5,0)); //markangle("$60^{\circ}$",radius=15,a,b); //markangle("$60^{\circ}$",radius=15,(1.5,0),(2.5,sqrt(3)),(1.5,0)); markangle(Label("$60^{\circ}$"),(1.5,0),(2.5,sqrt(3)),(3.5,0),radius=15); //markangle(Label("$60^{\circ}$"),(1.5,0),origin,(0,1),radius=20); [/asy]',
        "level": "Level 5",
        "type": "Geometry",
        "answer": "48.0",
        "solution": "The cross section of the cone is an equilateral triangle. The ratio of the base to the height of an equilateral triangle is 1 to $\sqrt{3}/2$. In terms of the radius, $r$, the base is $2r$ and the height is $2r\sqrt{3}/2$, or $r\sqrt{3}$. Since we know the volume of the cone, we can use the volume formula and solve the equation \[(1/3) times \pi times r^2 times r\sqrt{3} = 12288\pi\] for $r$. Dividing both sides of the equation by $\pi$ gives $(1/3)r^3\sqrt{3} = 12288$. Tripling both sides, we get $r^3\sqrt{3} = 36,\!864$. Now, we want $r\sqrt{3},$ so we multiply both sides by $3$ to get $r^3\cdot(\sqrt{3})^3 = (r\sqrt{3})^3 = 36,\!864 \cdot 3 = 110,\!592.$ Taking the cube root of both sides, we get $r\sqrt{3} = boxed{48.0}.$",
    },
    {
        "initial_question": "Triangle $ABC$ has vertices at $A(5,8)$, $B(3,-2)$, and $C(6,1)$. The point $D$ with coordinates $(m,n)$ is chosen inside the triangle so that the three small triangles $ABD$, $ACD$ and $BCD$ all have equal areas. What is the value of $10m + n$?",
        "level": "Level 5",
        "type": "Geometry",
        "answer": "49",
        "solution": "If $D$ is the centroid of triangle $ABC$, then $ABD$, $ACD$, and $BCD$ would all have equal areas (to see this, remember that the medians of a triangle divide the triangle into 6 equal areas). There is only one point with this property (if we move around $D$, the area of one of the small triangles will increase and will no longer be $1/3$ of the total area). So $D$ must be the centroid of triangle $ABC$. The $x$ and $y$ coordinates of the centroid are found by averaging the $x$ and $y$ coordinates, respectively, of the vertices, so $(m,n) = \left( \frac{5+3+6}{3}, \frac{8+(-2)+1}{3} \right) = \left( \frac{14}{3}, \frac{7}{3} \right)$, and $10m + n = 10 \left(\frac{14}{3}\right) + \frac{7}{3} = boxed{49}$.",
    },
    {
        "initial_question": "Six boys stood equally spaced on a circle of radius 40 feet. Each boy walked to all of the other non-adjacent persons on the circle, shook their hands and then returned to his original spot on the circle before the next boy started his trip to shake hands with all of the other non-adjacent boys on the circle. After all six boys had done this, what is the least distance in feet that could have been traveled? Express your answer in simplest radical form.",
        "level": "Level 5",
        "type": "Geometry",
        "answer": "boxed{480 + 480\sqrt{3}\ feet",
        "solution": "The thicker solid line in the diagram shows the shortest path that one person could travel. The circle is equally divided into six 60-degree arcs, so the short distance is 40 feet, the same as a radius. The dotted line is a diameter that separates the quadrilateral into two 30-60-90 triangles. The longer leg is $(80\sqrt {3})/2$, or $40\sqrt{3}$ feet. Each person travels $40\sqrt{3} + 40 + 40 + 40\sqrt{3} = 80 + 80\sqrt{3}$ feet. After all six people did this, $6(80 + 80\sqrt{3}) = boxed{480 + 480\sqrt{3}text{ feet}}$ had been traveled. [asy] import olympiad; import geometry; size(100); defaultpen(linewidth(0.8)); dotfactor=4; draw(unitcircle); for(int i = 0; i <= 6; ++i){ dot(dir(60*i + 30)); } draw(dir(30)--dir(90)--dir(150)--dir(270)--cycle); draw(dir(90)--dir(270),dotted); [/asy]",
    },
]
