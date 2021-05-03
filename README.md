# uqac-802-elevator-simulation
![](https://github.com/ethicnology/uqac-802-elevator-simulation/blob/main/logo.png "Screenshot")  
[Subject](https://github.com/ethicnology/uqac-802-elevator-simulation/blob/main/Projet.pdf)

## Installation
Pour utiliser notre programme, il est nécessaire de disposer de python 3 et d’installer l’environnement de simulation SimPy 4.0.1 et la dépendance NumPy.  
```sh
pip3 install simpy
pip3 install numpy
```

## Usage
Notre programme met à disposition une interface en ligne de commande (CLI) grâce à laquelle l’utilisateur peut modifier la valeur des paramètres par défaut, vous pouvez :  
* Choisir le nombre d’ascenseurs avec -e ou --elevators, default=1
* Choisir la capacité pour chaque ascenseur avec -c ou --capacity, default=1
* Choisir la vitesse de l’ascenseur pour passer d’un étage à l’autre avec -s ou --speed, default=10 (valeur par défaut dans le sujet)
* Sélectionner l'algorithme d’ordonnancement avec -a ou --algorithm, default=FCFS l’autre valeur utilisable est SSTF 
* Activer ou non le mode idle de l’ascenseur avec -i ou --idle, default=False si vous souhaitez activer ce mode utilisez -i True cependant, si vous souhaitez le désactiver supprimez simplement l’argument -i lors de l’exécution de la commande.
* Préciser la valeur de lambda dans le processus d’arrivée de Poisson avec -l ou --lambd, default=0.5 (valeur par défaut dans le sujet)
Spécifier la durée de la simulation avec -d ou --duration, default=10000

![](https://github.com/ethicnology/uqac-802-elevator-simulation/blob/main/cli_example.png "Example") 
![](https://github.com/ethicnology/uqac-802-elevator-simulation/blob/main/manual.png "Manual") 

## Results
Les résultats sont inscrits dans un fichier CSV qui porte en nom l'heure de l'exécution et l'ensemble des paramètres utilisés tels que :
```sh
16:35:44_elevators=2_capacity=5_speed=10_idle=True_algorithm=SSTF_lambda=0.5.csv
```