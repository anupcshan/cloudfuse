%.pb.cc: %.proto
	protoc --cpp_out=. $<

clean:
	rm -f *.o; rm -f *.pb.cc; rm -f *.pb.h
