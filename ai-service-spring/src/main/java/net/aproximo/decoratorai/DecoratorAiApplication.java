package net.aproximo.decoratorai;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.AutoConfiguration;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.jdbc.autoconfigure.DataSourceAutoConfiguration;

@SpringBootApplication(exclude = {DataSourceAutoConfiguration.class })

public class DecoratorAiApplication {

	public static void main(String[] args) {

		SpringApplication.run(DecoratorAiApplication.class, args);
	}

}
