package net.aproximo.decoratorai.model.dto;

public class ProductEntityCreationDto {


        @NotBlank(message = "Username is required!")
        @Size(min= 3, message = "Username must have atleast 3 characters!")
        @Size(max= 20, message = "Username can have have atmost 20 characters!")
        private String userName;

        @Email(message = "Email is not in valid format!")
        @NotBlank(message = "Email is required!")
        private String email;

        @NotBlank(message = "Phone number is required!")
        @Size(min = 10, max = 10, message = "Phone number must have 10 characters!")
        @Pattern(regexp="^[0-9]*$", message = "Phone number must contain only digits")
        private String phone;

    }
}
