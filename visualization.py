
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import matplotlib.patches as patches
from matplotlib.path import Path
import numpy as np
import time

fig, ax = plt.subplots(1, 1)
fig.set_size_inches(8,8)


robot_points = [(0,0), (0,0),(0,0),(0,0),(0,0)]
dash_points = [(0,0), (0,0),(0,0),(0,0),(0,0)]
ap_point=(0,0)
#line, = ax.plot([], [], lw=2)

def animate(i):
    #ax.clear()
    global robot_points
    global dash_points
    print(robot_points)
    if i==0:
        temp=str(robot_points[i][0])+','+str(robot_points[i][1])
        temp='Robot path starts at ('+temp+')'
        plt.text(robot_points[i][0]-0.9,robot_points[i][1]-0.2,temp)

        temp_2='('+str(dash_points[i][0])+','+str(dash_points[i][1])+')'
        plt.text(dash_points[i][0]-0.3,dash_points[i][1]-0.3,temp_2)
    if i==5:
        temp=str(ap_point[0])+','+str(ap_point[1])
        temp='Client device estimated at ('+temp+')'
        plt.text(ap_point[0]-0.5,ap_point[1]+0.5,temp)
    
    
    # Plot that point using the x and y coordinates
    if i in range(4):
        point = robot_points[i]
        ax.plot(point[0], point[1], color='green', 
                label='original', marker='o')
        dash_point=dash_points[i]
        ax.plot(dash_point[0], dash_point[1], color='gray', 
                label='original', marker='o')
    
    else:
        
        ax.plot(ap_point[0], ap_point[1], color='red', 
        label='original', marker='*')
    

    try:
        #ax.plot([robot_points[i][0],robot_points[i+1][0]], [robot_points[i][1],robot_points[i+1][1]], 'k-', lw=2)
        #ax.remove(robot_points[i-1][0],robot_points[i-1][1])
        ax.plot(np.linspace(robot_points[i][0],robot_points[i+1][0], 3), np.linspace(robot_points[i][1],robot_points[i+1][1], 3), 'k-', lw=2)
        ax.plot(np.linspace(dash_points[i][0],dash_points[i+1][0], 3), np.linspace(dash_points[i][1],dash_points[i+1][1], 3), 'k--', lw=2)
        #ax.arrow(robot_points[i][0],robot_points[i][1],1,0,width=0.1, head_width=0.1)
    except:
        pass


def plot_robo_traj(x1,y1,x2,y2,x_dash,y_dash,path):
    global robot_points
    global ap_point
    global dash_points
    if path ==0:
        robot_points=[(x1,y1),(x1,y1+1),(x1+1,y1+1),(x1+1,y1)]
        dash_points=[(x_dash,y_dash),(x_dash,y_dash+1),(x_dash+1,y_dash+1),(x_dash+1,y_dash)]
    elif path ==1:
        robot_points=[(x1,y1),(x1,y1+2),(x1+2,y1+2),(x1+2,y1)]
        dash_points=[(x_dash,y_dash),(x_dash,y_dash+2),(x_dash+2,y_dash+2),(x_dash+2,y_dash)]
    elif path ==2:
        robot_points=[(x1,y1),(x1,y1+4),(x1+2,y1+4),(x1+2,y1)]
        dash_points=[(x_dash,y_dash),(x_dash,y_dash+4),(x_dash+2,y_dash+4),(x_dash+2,y_dash)]
    ap_point=[x2,y2]
    ax.set_xlim([0, max(x1+4,x2+4,y1+4, y2+4, y_dash+4,x_dash+4 )])
    ax.set_ylim([0, max(x1+4,x2+4,y1+4, y2+4, y_dash+4,x_dash+4)])
    

    ani = FuncAnimation(fig, animate, frames=6,
                        interval=800, repeat=False)
    plt.xlabel("x (m)")
    plt.ylabel("y (m)")
    ani.save('updated.gif')
    plt.show()

    

def main():
    plot_robo_traj(1,1.5, 7,12,3,4,path=1)



if __name__ == '__main__':
    main()