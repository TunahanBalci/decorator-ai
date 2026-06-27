package net.aproximo;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration(proxyBeanMethods = false)
public class MyDataSourceConfiguration {

	@Bean
	@ConfigurationProperties("app.datasource")
	public SomeDataSource dataSource() {
		return new SomeDataSource();
	}

}