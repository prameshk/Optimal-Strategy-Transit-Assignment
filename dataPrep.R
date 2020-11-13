#########################################################
# The script creates a static transit network from the 
# GTFS data suitable for optimal strategy transit assignment
##########################################################
# Script created by Pramesh Kumar 12/19/2018
##########################################################

loc <- "Z:\\Projects\\TNDP\\TransitNetworkDesign\\Scripts\\Optimal strategy assignment\\GTFS\\" # Location of the 
loc2 <- "Z:\\Projects\\Ride Sharing with Transit\\SBSP\\Schedule-based-transit-shortest-path\\test network GTFS\\"

options(stringsAsFactors = FALSE)
routes <- read.table(unz(paste0(loc,"gtfs.zip"), "routes.txt"), header=T, quote="\"", sep=",")
stops <- read.table(unz(paste0(loc,"gtfs.zip"), "stops.txt"), header=T, quote="\"", sep=",")
transfers <- read.table(unz(paste0(loc,"gtfs.zip"), "transfers.txt"), header=T, quote="\"", sep=",")
trips <- read.table(unz(paste0(loc,"gtfs.zip"), "trips.txt"), header=T, quote="\"", sep=",")
stopTimes <- read.table(unz(paste0(loc,"gtfs.zip"), "stop_times.txt"), header=T, quote="\"", sep=",")

# Creating nodes for the network
nodes <- stops[c('stop_id', 'stop_name', 'stop_lat', 'stop_lon')]
nodes$type <- "stop" # If the node is just a boarding/alighting location

mergeData <- merge(stopTimes, trips, by="trip_id")
stopRoute <- unique(mergeData[c('stop_id', 'route_id')])
stopRoute <- unique(merge(stops, stopRoute, "stop_id"))
stopRoute <- stopRoute[c('stop_id', 'stop_name', 'stop_lat', 'stop_lon', 'route_id')]
colnames(stopRoute) <- c('stop_id', 'stop_name', 'stop_lat', 'stop_lon', 'type')
nodes <- rbind(nodes, stopRoute)
nodes <- unique(nodes)


# Creating links for the network

# A function to convert the time into seconds
ConvertToSeconds <- function(X)
{
  X <- strsplit(X, ":")
  sapply(X, function(Y) sum(as.numeric(Y) * c(3600, 60, 1)))
}


gtfs <- merge(stopTimes, trips, by = "trip_id")
gtfs <- merge(gtfs, routes, by ="route_id")
Ind <- which(substr(gtfs$trip_id, nchar(gtfs$trip_id) - 9, nchar(gtfs$trip_id)) == "Weekday-01")
gtfs <- gtfs[(Ind), ]
gtfs$headway <- 10

for (r in routes$route_id){
  Ind <- which(gtfs$route_id == r)
  st <- gtfs[Ind, ]
  st <- st[st$stop_sequence == 1, ]
  st$departure_time <- ConvertToSeconds(st$departure_time)
  st <- st[order(st$departure_time), ]
  gtfs[Ind, ]$headway <- round(mean(st[-1,]$departure_time - st[-nrow(st),]$departure_time)/60)
}

trips <- c()
for (r in routes$route_id){
  trips <- c(trips, gtfs[gtfs$route_id == r, ]$trip_id[1])
}


gtfs <- gtfs[gtfs$trip_id %in% trips, ]
gtfs <- gtfs[order(gtfs$route_id,gtfs$stop_sequence), ]
gtfs <- gtfs[,c("route_id", "trip_id", "departure_time", "stop_id", "stop_sequence", "timepoint", "service_id", "trip_headsign", "direction_id", "shape_id", "route_short_name", "route_long_name", "headway") ]

# Writing files
write.table(nodes, paste0(loc, "nodes.dat"), sep = "\t", row.names = FALSE, quote = FALSE)
write.table(gtfs, paste0(loc, "links.dat"), sep = "\t", row.names = FALSE, quote = FALSE)


dem <- read.csv("Z:\\Projects\\Data\\Minneapolis - St. Paul network\\Demand\\trips_fullOD.csv",header=T)
dem <- aggregate(Trips~Origin+Destination, dem, sum)
write.table(dem, paste0(loc, "demand.dat"), sep = "\t", row.names = FALSE, quote = FALSE)


